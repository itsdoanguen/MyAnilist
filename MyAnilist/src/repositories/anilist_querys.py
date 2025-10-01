ANIME_INFO_QS = '''
query ($id: Int) {
    Media(id: $id, type: ANIME) {
      id
      title { romaji english }
      startDate { year month day }
      endDate { year month day }
      coverImage { large }
      bannerImage
      format
      status
      episodes
      season
      description
      averageScore
      genres
      nextAiringEpisode { airingAt timeUntilAiring episode }
    }
}
'''


ANIME_ID_SEARCH_QS = '''
query ($query: String, $page: Int, $perpage: Int) {
    Page (page: $page, perPage: $perpage) {
      pageInfo { total currentPage lastPage hasNextPage }
      media (search: $query, type: ANIME) {
        id
        title { romaji english }
        coverImage { large }
        averageScore
        popularity
        episodes
        season
        isAdult
      }
    }
}
'''


ANIME_SEASON_TREND_QS = '''
query ($season: MediaSeason, $seasonYear: Int, $page: Int, $perpage: Int, $sort: [MediaSort]) {
  Page(page: $page, perPage: $perpage) {
    pageInfo { total currentPage lastPage hasNextPage }
    media(season: $season, seasonYear: $seasonYear, type: ANIME, sort: $sort) {
      id
      title { romaji english }
      coverImage { large }
      bannerImage
      averageScore
      popularity
      episodes
      season
      isAdult
      nextAiringEpisode { airingAt timeUntilAiring episode }
      trending
    }
  }
}
'''



ANIME_SEARCH_CRITERIA_QS = '''
query ($genres: [String], $season: MediaSeason, $seasonYear: Int, $format: MediaFormat, $status: MediaStatus, $page: Int, $perpage: Int, $sort: [MediaSort]) {
  Page(page: $page, perPage: $perpage) {
    pageInfo { total currentPage lastPage hasNextPage }
    media(genre_in: $genres, season: $season, seasonYear: $seasonYear, format: $format, status: $status, type: ANIME, sort: $sort) {
      id
      title { romaji english }
      coverImage { large }
      bannerImage
      averageScore
      popularity
      episodes
      season
      genres
      isAdult
      nextAiringEpisode { airingAt timeUntilAiring episode }
      trending
    }
  }
}
'''
