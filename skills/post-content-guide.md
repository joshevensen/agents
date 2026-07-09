# Post Content Guide

Use this guide in the background when developing, writing, reviewing, or refreshing posts. Do not present it to the user as a form.

## Title and Slug

- Target a title under 60 characters for search display. Never exceed 73 characters.
- Use book title capitalization.
- Derive the slug by lowercasing the title, removing every non-alphanumeric character except spaces, replacing spaces with hyphens, collapsing repeated hyphens, trimming leading and trailing hyphens, and truncating to 73 characters.
- Confirm the final title and slug before creating a branch or directory.

## Word Counts

- Response: approximately 1,350 words.
- Staple: approximately 2,500 words.
- Pillar: approximately 3,500 words.

Treat these as scope targets, not reasons to pad thin material.

## Post Recipe

### 1. Title

State the topic or question plainly. Match the reader's search intent and avoid clever wording that obscures the subject.

### 2. Lead In

Write two or three sentences that show the reader they are in the right place and establish confidence. Make this usable as the meta description: concrete, accurate, and free of throat-clearing.

### 3. Answer Section

Give the direct answer in no more than 300 characters. Make it self-contained and suitable for a search snippet. Write this section last, after the full post is known, then place it after the lead in.

### 4. Read On

Use one to three sentences to explain what useful detail comes next. Create momentum without generic transitions such as "in this post" or "let's dive in."

### 5. First Subhead

Use an H2 that directly advances the main topic. Do not repeat the title verbatim.

### 6. Detailed Answer

Deliver the most complete answer to the main question. Explain qualifications, tradeoffs, examples, and practical consequences. Fulfill every promise made by the title, lead in, answer section, and outline.

### 7. More Information

Add focused H2 sections that anticipate the reader's next questions while remaining on topic. Order sections by usefulness, not by the order research was discovered.

### 8. FAQ

Use concise question-and-answer H2 or H3 sections only when allowed by the post type. Each answer must add information rather than repeat earlier sections.

## Rules by Post Type

| Element | Response | Staple | Pillar |
|---|---|---|---|
| Base recipe | Required | Required | Required |
| Scope | One narrow intent | Durable topic coverage | Broad authoritative coverage |
| More Information | Focused and limited | Robust | Robust and comprehensive |
| FAQ | Omit | Optional when natural questions remain | Required |
| Typical depth | Quick, complete answer | Long-lived practical resource | Definitive topic resource |

Response posts must not drift into adjacent search intents. Staple posts may cover natural follow-up decisions and comparisons. Pillar posts should map the topic comprehensively while keeping each section useful to the central reader intent.

## Specificity and Evidence

- Name real entities when relevant: providers, products, standards, technologies, agencies, locations, plans, and measurable thresholds.
- Prefer concrete examples over generic categories.
- Verify factual and date-sensitive claims with credible sources during research.
- Do not invent statistics, quotations, product details, or source conclusions.
- Add `<!-- REFRESH-CHECK -->` inline beside every claim likely to change, including prices, plan availability, market rankings, regulations, product specifications, coverage figures, and current recommendations.

Example:

```markdown
The provider's entry plan costs $50 per month. <!-- REFRESH-CHECK -->
```

The marker belongs next to the complete claim so a later refresh can evaluate it in context.

## Paragraphs and Formatting

- Keep paragraphs conversational and no longer than six rendered lines.
- Vary sentence and paragraph length naturally.
- Use descriptive H2 and H3 headings that help readers scan.
- Use lists for genuine sequences or sets, tables for comparisons, and blockquotes only for short attributed quotations.
- Break dense sections with useful formatting, not decorative filler.
- Avoid generic introductions, repetitive conclusions, empty transitions, keyword stuffing, and AI-sounding summary phrases.
- Keep prose focused on the main topic. Remove sections that exist only to reach a word count.
- Write `post.md` as pure prose with no frontmatter; metadata belongs in `meta.yaml`.
