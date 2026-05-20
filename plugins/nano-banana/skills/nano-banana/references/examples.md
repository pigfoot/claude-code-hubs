# Example Workflows

## Scenario 1: First Generation (Auto Seed)

```
User: "Generate a modern office interior"

Assistant actions:
1. Create config WITHOUT seed (auto-generate):
   {
     "slides": [{"number": 1, "prompt": "Modern office interior with natural lighting"}],
     "output_dir": "./001-office-design/"
   }
2. Execute: uv run --managed-python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py --config {temp_config}
3. Read results: ./001-office-design/generation-results.json
   → {"outputs": [{"slide": 1, "path": "slide-01.png", "seed": 392664860}]}
4. Report to user: "Generated at ./001-office-design/slide-01.png (seed: 392664860)"
```

## Scenario 2: Reproduce Previous Image

```
User: "I love that office image! Regenerate it with seed 392664860"

Assistant actions:
1. Create config WITH seed:
   {
     "slides": [{"number": 1, "prompt": "Modern office interior with natural lighting", "seed": 392664860}],
     "output_dir": "./002-office-design-v2/"
   }
2. Execute script
3. Result: Visually identical image
```

## Scenario 3: Explore Variations

```
User: "Generate 3 variations of a robot holding flowers, use different temperatures"

Assistant actions:
1. Create config with per-slide temperatures:
   {
     "seed": 42,
     "slides": [
       {"number": 1, "prompt": "A cute robot holding flowers", "temperature": 0.5},
       {"number": 2, "prompt": "A cute robot holding flowers", "temperature": 1.0},
       {"number": 3, "prompt": "A cute robot holding flowers", "temperature": 1.5}
     ],
     "output_dir": "./003-robot-variations/"
   }
2. Execute script
3. Result: 3 different compositions (temperature effect)
```

## Scenario 4: Batch with Consistent Style

```
User: "Create 5 presentation slides with TrendLife style, use same seed"

Assistant actions:
1. Create config with global seed and appropriate layout for each slide:
   {
     "seed": 12345,
     "slides": [
       {"number": 1, "prompt": "AI Safety: Building Secure Systems", "style": "trendlife", "layout": "featured"},
       {"number": 2, "prompt": "Key features overview", "style": "trendlife", "layout": "content"},
       {"number": 3, "prompt": "Technical architecture", "style": "trendlife", "layout": "content"},
       {"number": 4, "prompt": "Use cases and benefits", "style": "trendlife", "layout": "content"},
       {"number": 5, "prompt": "Thank You - Contact Us", "style": "trendlife", "layout": "featured"}
     ],
     "output_dir": "./004-ai-safety-deck/"
   }
2. Execute in background (5+ slides)
3. Monitor progress file
4. Results:
   - Slide 1 (featured): Logo integrated naturally by AI into title design
   - Slides 2-4 (content): Logo overlaid in bottom-right corner
   - Slide 5 (featured): Logo integrated naturally by AI into closing design
   - All slides use seed 12345 for visual consistency
```
