SELECT
    w.german_word,
    w.meaning,
    w.notes,
    json_agg(
        json_build_object(
            'sentence_de', s.sentence_de,
            'sentence_en', s.sentence_en
        )
    ) AS sentences,
    MAX(fv.viewed_at) AS last_viewed
FROM words w
LEFT JOIN example_sentences s ON s.word_id = w.id
LEFT JOIN flashcard_views fv ON fv.word_id = w.id
WHERE w.enrichment_status = 'completed'
GROUP BY w.id
ORDER BY last_viewed ASC NULLS FIRST   -- unseen words first, then least recently seen
LIMIT 20;