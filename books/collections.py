COLLECTIONS = {
  "crime-mystery-thrillers": {
    "title": "Crime, Mystery & Thrillers",
    "description": "Gripping mysteries, crime novels and page-turning thrillers.",
    "tags": [
      "crime", "mystery", "thriller", "suspense",
      "police procedural", "cosy mystery",
      "nordic noir", "tartan noir",
      "psychological thriller", "spy fiction",
      "legal story", "techno-thriller",
      "historical mystery"
    ],
    "min_match": 2,
    "featured": True,
    "exclude_categories": ["Non-fiction"],
    "filters": [
        {
            "key": "cosy-mysteries",
            "title": "Cosy Mysteries",
            "tags": ["cosy mystery"],
        },
        {
            "key": "historical-mysteries",
            "title": "Historical Mysteries",
            "tags": ["historical mystery"],
        },
        {
            "key": "police-procedurals",
            "title": "Police Procedurals",
            "tags": ["police procedural"],
        },
        {
            "key": "tartan-noir",
            "title": "Tartan Noir",
            "tags": ["tartan noir"],
        },
        {
            "key": "nordic-noir",
            "title": "Nordic Noir",
            "tags": ["nordic noir"],
        },
        {
            "key": "psychological-thrillers",
            "title": "Psychological Thrillers",
            "tags": ["psychological thriller", "psychological fiction"],
        },
        {
            "key": "spy-fiction",
            "title": "Spy Fiction",
            "tags": ["spy fiction"],
        },
    ],
  },

  "fantasy-sci-fi": {
    "title": "Fantasy & Sci-Fi",
    "description": "Epic fantasy, science fiction and imaginative worlds.",
    "tags": [
      "fantasy", "sci-fi", "epic fantasy",
      "dystopian", "post-apocalyptic",
      "time travel", "space opera", "steampunk",
      "aliens", "biotech"
    ],
    "min_match": 1,
    "featured": True,
    "exclude_categories": ["Non-fiction"],
    "filters": [
        {
            "key": "epic-fantasy",
            "title": "Epic Fantasy",
            "tags": ["epic fantasy"],
        },
        {
            "key": "dystopian",
            "title": "Dystopian",
            "tags": ["dystopian"],
        },
        {
            "key": "post-apocalyptic",
            "title": "Post-apocalyptic",
            "tags": ["post-apocalyptic"],
        },
        {
            "key": "space-opera",
            "title": "Space Opera",
            "tags": ["space opera"],
        },
    ],
  },

  "historical-fiction": {
    "title": "Historical Fiction",
    "description": "Stories set well in the past, blending fictional characters with well researched detail about the period.",
    "tags": [
      "historical fiction"
    ],
    "min_match": 1,
    "featured": True,
    "exclude_categories": ["Non-fiction"],
    "filters": [
        {
            "key": "ancient-world",
            "title": "Ancient World",
            "tags": ["ancient world"],
        },
        {
            "key": "medieval",
            "title": "Medieval",
            "tags": ["medieval"],
        },
        {
            "key": "tudor",
            "title": "Tudor",
            "tags": ["tudor"],
        },
        {
            "key": "victorian",
            "title": "Victorian",
            "tags": ["victorian"],
        },
        {
            "key": "world-wars",
            "title": "World Wars",
            "tags": ["world war i", "world war ii"],
        },
    ],
  },

  "war-fiction": {
    "title": "War, Home Front & Military Fiction",
    "description": "Stories of conflict, courage and survival - from battlefield action to civilian life during wartime.",
    "tags": [
      "war story", "homefront", "military fiction",
      "world war i", "world war ii", "holocaust"
    ],
    "min_match": 1,
    "exclude_categories": ["Non-fiction"],
    "filters": [
        {
            "key": "world-wars",
            "title": "World Wars",
            "tags": ["world war i", "world war ii"],
        },
        {
            "key": "military-fiction",
            "title": "Military Fiction",
            "tags": ["military fiction"],
        },
        {
            "key": "homefront",
            "title": "Home Front",
            "tags": ["homefront"],
        },
    ],
  },

  "place-culture-identity": {
    "title": "Place, Culture & Identity",
    "description": "Books shaped by culture, identity and setting - from cross-cultural stories to vivid sense-of-place reads.",
    "tags": [
      "sense of place", "cross-cultural",
      "black authors", "lgbt", "feminism",
      "society"
    ],
    "min_match": 1,
    "filters": [
        {
            "key": "sense-of-place",
            "title": "Sense Of Place",
            "tags": ["sense of place"],
        },
        {
            "key": "cross-cultural",
            "title": "Cross-Cultural",
            "tags": ["cross-cultural"],
        },
        {
            "key": "lgbt",
            "title": "LGBT",
            "tags": ["lgbt"],
        },
    ],
  },

  "romance-love-stories": {
    "title": "Romance & Love Stories",
    "description": "Love stories and romantic fiction - funny, heartfelt and escapist.",
    "tags": [
      "romance", "chick lit", "new adult",
      "historical romance", "paranormal romance",
      "erotica"
    ],
    "min_match": 1,
    "featured": True,
    "exclude_categories": ["Non-fiction"],
    "filters": [
        {
            "key": "chick-lit",
            "title": "Chick Lit",
            "tags": ["chick lit"],
        },
        {
            "key": "historical-romance",
            "title": "Historical Romance",
            "tags": ["historical romance"],
        },
        {
            "key": "paranormal-romance",
            "title": "Paranormal Romance",
            "tags": ["paranormal romance"],
        },
        {
            "key": "erotica",
            "title": "Erotica",
            "tags": ["erotica"],
        },
    ],
  },

  "family-relationships": {
    "title": "Family & Relationships",
    "description": "Domestic drama, family life and the messy business of human connection.",
    "tags": [
      "family drama", "relationships",
      "abuse", "mental health"
    ],
    "min_match": 1,
    "exclude_categories": ["Non-fiction"],
    "filters": [
        {
            "key": "family-drama",
            "title": "Family Drama",
            "tags": ["family drama"],
        },
        {
            "key": "relationships",
            "title": "Relationships",
            "tags": ["relationships"],
        },
        {
            "key": "abuse",
            "title": "Abuse",
            "tags": ["abuse"],
        },
        {
            "key": "mental-health",
            "title": "Mental Health",
            "tags": ["mental health"],
        },
    ],
  },

  "literary-psychological-fiction": {
    "title": "Literary & Psychological Fiction",
    "description": "Thought-provoking fiction that explores the inner lives of characters and the human condition.",
    "tags": [
      "literary fiction", "psychological fiction",
      "postmodern literature", "magical realism",
      "bildungsroman"
    ],
    "min_match": 1,
    "exclude_categories": ["Non-fiction"],
    "filters": [
        {
            "key": "literary-fiction",
            "title": "Literary Fiction",
            "tags": ["literary fiction"],
        },
        {
            "key": "psychological-fiction",
            "title": "Psychological Fiction",
            "tags": ["psychological fiction"],
        },
        {
            "key": "bildungsroman",
            "title": "Coming Of Age",
            "tags": ["bildungsroman"],
        },
        {
            "key": "magical-realism",
            "title": "Magical Realism",
            "tags": ["magical realism"],
        },
    ],
  },

  "adventure-action": {
    "title": "Adventure & Action",
    "description": "Fast-paced, high-stakes stories featuring physical thrills, perilous journeys, and daring exploits.",
    "tags": [
      "adventure", "action", "westerns"
    ],
    "min_match": 1,
    "exclude_categories": ["Non-fiction"],
    "filters": [
        {
            "key": "adventure",
            "title": "Adventure",
            "tags": ["adventure"],
        },
        {
            "key": "action",
            "title": "Action",
            "tags": ["action"],
        },
        {
            "key": "westerns",
            "title": "Westerns",
            "tags": ["westerns"],
        },
    ],
  },

  "supernatural-fiction": {
    "title": "Supernatural Fiction",
    "description": "Ghosts, vampires, demons, magical beings, or other phenomena beyond ordinary reality/science.",
    "tags": [
      "supernatural",
      "ghosts", "vampires", "witches",
      "angels and demons"
    ],
    "min_match": 1,
    "exclude_categories": ["Non-fiction"],
    "filters": [
        {
            "key": "ghosts",
            "title": "Ghost Stories",
            "tags": ["ghosts"],
        },
        {
            "key": "vampires",
            "title": "Vampire Lore",
            "tags": ["vampires"],
        },
        {
            "key": "witches",
            "title": "Witch Lit",
            "tags": ["witches"],
        },
        {
            "key": "angels-demons",
            "title": "Angels and Demons",
            "tags": ["angels and demons"],
        },
    ],
  },

  "humour-satire": {
    "title": "Humour & Satire",
    "description": "Sharp, witty and laugh-out-loud books that skewer society, politics and everyday life.",
    "tags": [
      "humour", "satire"
    ],
    "min_match": 1,
  },

  "memoir-life-stories": {
    "title": "Memoir & Life Stories",
    "description": "Personal stories, reflections and lived experiences.",
    "tags": [
        "memoir", "biography"
    ],
    "min_match": 1,
    "include_categories": ["Non-fiction"],
  },

  "books-film-tv": {
    "title": "From Page to Screen",
    "description": "Books that made the leap from page to film or television.",
    "tags": [
      "adapted to screen", "novelisation"
    ],
    "min_match": 1,
  },

  "short-fiction": {
    "title": "Short Stories & Novellas",
    "description": "Concise stories with focused narratives.",
    "tags": [
      "short stories", "novella"
    ],
    "min_match": 1,
    "filters": [
        {
            "key": "short-stories",
            "title": "Short Stories",
            "tags": ["short stories"],
        },
        {
            "key": "novella",
            "title": "Novellas",
            "tags": ["novella"],
        },
    ],
  },

  "children-young-adult": {
    "title": "Children's & Young Adult",
    "description": "Beloved children's stories and young adult fiction for curious, adventurous readers.",
    "tags": [
      "children's", "middle grade",
      "teen", "young adult"
    ],
    "min_match": 1,
    "filters": [
        {
            "key": "children-middle-grade",
            "title": "Children's to Middle Grade",
            "tags": ["children's", "middle grade"],
        },
        {
            "key": "teen-ya",
            "title": "Teen to YA",
            "tags": ["teen", "young adult"],
        },
    ],
  },

  "classics": {
    "title": "Classics",
    "description": "Enduring works that are widely regarded as part of the literary canon.",
    "tags": [
      "classics"
    ],
    "min_match": 1,
  },
}

# Potential additions:
# ADDITIONAL = {
#   "history-war-crime": {
#     "title": "History, War & True Crime",
#     "description": "",
#     "tags": [
#       "history", "british history",
#       "world war i", "world war ii",
#       "holocaust", "true crime"
#     ],
#     "min_match": 1,
#     "include_categories": ["Non-fiction"],
#   },

#   "food-travel-arts-interests": {
#     "title": "Food, Travel, Arts & Interests",
#     "tags": [
#       "travel", "food and drink", "music and arts",
#       "animals", "sports", "environment",
#       "horticulture"
#     ],
#     "min_match": 1,
#     "include_categories": ["Non-fiction"],
#   }
# }