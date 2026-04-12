# Deep Research Agent - Architecture

## Vue d'ensemble

Agent de recherche approfondie construit avec **LangGraph** et les modèles **Google Gemini**. Il prend une question utilisateur, effectue des recherches web itératives, identifie les lacunes dans les informations collectées, et produit une réponse sourcée en markdown.

## Stack technique

| Composant | Technologie |
|---|---|
| Orchestration | LangGraph (StateGraph) |
| LLMs | Gemini 2.0 Flash, Gemini 2.5 Flash, Gemini 2.5 Pro |
| Recherche web | Google Search API (native via `google.genai`) |
| Framework LLM | LangChain / LangChain Google GenAI |
| Validation des sorties | Pydantic (structured output) |

## Architecture du graphe

```
START
  │
  ▼
┌─────────────────┐
│ generate_query   │  ← Gemini 2.0 Flash
│ (1 instance)     │
└────────┬────────┘
         │  fan-out (Send) : 1 instance par query générée
         ▼
┌─────────────────┐
│ web_research     │  ← Gemini 2.0 Flash + Google Search tool
│ (N instances     │
│  en parallèle)   │
└────────┬────────┘
         │  fan-in
         ▼
┌─────────────────┐
│ reflection       │  ← Gemini 2.5 Flash
│ (1 instance)     │
└────────┬────────┘
         │
         ├── suffisant ──────────────┐
         │                           ▼
         │                  ┌─────────────────┐
         │                  │ finalize_answer   │  ← Gemini 2.5 Pro
         │                  └────────┬────────┘
         │                           │
         │                           ▼
         │                          END
         │
         └── lacunes détectées ──► web_research (nouvelle boucle)
                                   puis reflection...
```

## Noeuds en détail

### 1. `generate_query` — Génération de requetes de recherche

- **Modele** : Gemini 2.0 Flash
- **Entree** : Question utilisateur (depuis `messages`)
- **Sortie** : Liste de `Query` (query + rationale)
- **Structured output** : `SearchQueries` (Pydantic) force le LLM a retourner un JSON avec `queries` et `rationale`
- Le nombre max de queries est configurable via `initial_search_query_count`

### 2. `web_research` — Recherche web (executee en parallele)

- **Modele** : Gemini 2.0 Flash avec l'outil natif Google Search
- **Entree** : Une seule query (`WebSearchState`)
- **Sortie** : Texte enrichi de citations + sources formatees
- Utilise directement le client `google.genai` (pas LangChain) pour beneficier du `grounding_metadata`
- Les URLs longues de Vertex AI Search sont raccourcies via `resolve_urls()` pour economiser des tokens
- Les citations sont extraites et inserees dans le texte via `get_citations()` et `insert_citation_markers()`

### 3. `reflection` — Analyse des lacunes

- **Modele** : Gemini 2.5 Flash (plus intelligent pour l'analyse critique)
- **Entree** : Tous les resultats de recherche agreges + question originale
- **Sortie** : `ReflectionState` (`is_sufficient`, `knowledge_gap`, `follow_up_queries`)
- Incremente `research_loop_count` a chaque passage
- Si les infos sont insuffisantes ET que la limite de boucles n'est pas atteinte, de nouvelles recherches sont lancees

### 4. `finalize_answer` — Generation de la reponse finale

- **Modele** : Gemini 2.5 Pro (le plus capable, pour la synthese finale)
- **Entree** : Tous les resultats de recherche + question originale
- **Sortie** : Reponse markdown avec sources (URLs longues restaurees)
- Remplace les URLs courtes par les URLs originales dans le texte final
- Deduplique les sources utilisees

## Gestion de l'etat

L'`OverallState` est le state partage entre tous les noeuds :

| Champ | Type | Reduceur | Role |
|---|---|---|---|
| `messages` | list | `add_messages` | Historique de conversation |
| `search_query` | list | `operator.add` | Queries executees |
| `web_research_result` | list | `operator.add` | Resultats de recherche (texte + citations) |
| `sources_gathered` | list | `operator.add` | Sources {label, short_url, value} |
| `initial_search_query_count` | int | remplace | Nb max de queries initiales |
| `max_research_loops` | int | remplace | Limite de boucles de recherche |
| `research_loop_count` | int | remplace | Compteur de boucles |

Les reduceurs `add_messages` et `operator.add` permettent aux noeuds paralleles de contribuer leurs resultats sans ecraser ceux des autres.

## Routage conditionnel

Deux edges conditionnels controlent le flux :

1. **`generate_query` → `web_research`** : Fan-out via `Send()` — une instance de `web_research` par query generee
2. **`reflection` → `web_research` | `finalize_answer`** : Si les infos sont suffisantes ou que la limite de boucles est atteinte → `finalize_answer`. Sinon → nouvelles instances paralleles de `web_research` avec les follow-up queries

## Fichiers

| Fichier | Role |
|---|---|
| `deep_research_agent.py` | Graphe LangGraph principal (noeuds, edges, state) |
| `prompts.py` | Tous les prompts systeme des 4 noeuds |
| `utils.py` | Fonctions utilitaires (parsing URLs, citations, CLI) |
| `langgraph.json` | Configuration pour le deploiement LangGraph |
| `outputs/` | Graphe PNG et reponse markdown generee |

## Utilisation

```bash
python deep_research_agent.py "Quelle est la question ?" --initial-queries 3 --max-loops 2
```

La reponse est ecrite dans `outputs/deep_research_agent_response.md`.
