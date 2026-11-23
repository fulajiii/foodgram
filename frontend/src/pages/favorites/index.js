import { Card, Title, Pagination, CardList, Container, Main, CheckboxGroup  } from '../../components'
import styles from './styles.module.css'
import { useRecipes } from '../../utils/index.js'
import { useEffect, useState } from 'react'
import api from '../../api'
import MetaTags from 'react-meta-tags'

const Favorites = ({ updateOrders }) => {
  const {
    recipes,
    setRecipes,
    recipesCount,
    setRecipesCount,
    recipesPage,
    setRecipesPage,
    tagsValue,
    handleTagsChange,
    setTagsValue,
    handleAddToCart
  } = useRecipes()

  const [refresh, setRefresh] = useState(0)

  useEffect(() => {
    let current = true
    api
      .getRecipes({ page: recipesPage, is_favorited: 1, tags: tagsValue })
      .then(({ results, count }) => {
        if (current) {
          setRecipes(results)
          setRecipesCount(count)
        }
      })
      .catch(({ detail, errors }) => {
        if (!current) return
        if (detail && recipesPage > 1) {
          setRecipesPage(recipesPage - 1)
        } else if (errors || detail) {
          alert(errors || detail)
        }
      })
    return () => {
      current = false
    }
  }, [recipesPage, tagsValue, refresh, setRecipes, setRecipesCount, setRecipesPage])

  const removeFavorite = ({ id }) => {
    api.removeFromFavorites({ id })
      .then(() => {
        setRecipes(current => current.filter(recipe => recipe.id !== id))
        setRefresh(current => current + 1)
      })
      .catch(({ errors }) => {
        if (errors) alert(errors)
      })
  }

  useEffect(_ => {
    api.getTags()
      .then(tags => {
        setTagsValue(tags.map(tag => ({ ...tag, value: true })))
      })
  }, [])


  return <Main>
    <Container>
      <MetaTags>
        <title>Избранное</title>
        <meta name="description" content="Фудграм - Избранное" />
        <meta property="og:title" content="Избранное" />
      </MetaTags>
      <div className={styles.title}>
        <Title title='Избранное' />
        <CheckboxGroup
          values={tagsValue}
          handleChange={value => {
            setRecipesPage(1)
            handleTagsChange(value)
          }}
        />
      </div>
      {recipes.length > 0 && <CardList>
        {recipes.map(card => <Card
          {...card}
          key={card.id}
          updateOrders={updateOrders}
          handleLike={removeFavorite}
          handleAddToCart={handleAddToCart}
        />)}
      </CardList>}
      <Pagination
        count={recipesCount}
        limit={6}
        page={recipesPage}
        onPageChange={page => setRecipesPage(page)}
      />
    </Container>
  </Main>
}

export default Favorites

