# Advanced Gemini Image Generation Guide

This guide covers advanced scenarios for Gemini image generation including thinking process, Google Search grounding, and multi-turn conversations.

## Thinking Process

The model uses internal reasoning for complex prompts. It generates interim thought images to refine composition before producing the final output.

### Accessing Thoughts

```bash
uv run - << 'EOF'
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
from pathlib import Path
from google import genai
from google.genai import types

# Output directory - Claude sets based on user request (format: NNN-short-name)
OUTPUT_DIR = Path("001-futuristic-city")  # <-- Claude replaces this dynamically
OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=["Create a detailed architectural blueprint of a futuristic city"],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
    )
)

for part in response.parts:
    if part.thought:
        if part.text:
            print(f"Thought: {part.text}")
        elif image := part.as_image():
            image.save(OUTPUT_DIR / "thought.png")
            print(f"Thought image saved to {OUTPUT_DIR}/thought.png")
    elif part.inline_data is not None:
        output_path = OUTPUT_DIR / "output.png"
        part.as_image().save(output_path)
        print(f"Saved: {output_path}")
    elif part.text:
        print(part.text)
EOF
```

### Thought Signatures

Thought signatures are encrypted representations of the model's internal thought process. They preserve reasoning context across multi-turn interactions for consistent iterative refinement.

## Google Search Grounding

Generate images based on real-time information like weather forecasts, stock data, or current events.

### Basic Search Grounding

```bash
uv run - << 'EOF'
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
from pathlib import Path
from google import genai
from google.genai import types

# Output directory - Claude sets based on user request (format: NNN-short-name)
OUTPUT_DIR = Path("001-weather-chart")  # <-- Claude replaces this dynamically
OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=["Visualize current weather for San Francisco as a chart"],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        tools=[{"google_search": {}}]
    )
)

for part in response.parts:
    if part.text:
        print(part.text)
    elif part.inline_data is not None:
        output_path = OUTPUT_DIR / "weather_chart.png"
        part.as_image().save(output_path)
        print(f"Saved: {output_path}")

# Access grounding metadata if available
if hasattr(response, 'grounding_metadata'):
    print(f"Sources: {response.grounding_metadata}")
EOF
```

### Use Cases for Search Grounding

- Weather visualizations and forecasts
- Stock market charts and financial data
- Current events infographics
- Historical maps with accurate data
- Scientific diagrams requiring verified facts

**Note:** Image-based search results are not passed to the generation model.

## Multi-Turn Conversations

Use chat sessions for iterative image refinement across multiple turns.

### Chat-Based Editing

```bash
uv run - << 'EOF'
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
from pathlib import Path
from google import genai
from google.genai import types

# Output directory - Claude sets based on user request (format: NNN-short-name)
OUTPUT_DIR = Path("001-photosynthesis")  # <-- Claude replaces this dynamically
OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client()

chat = client.chats.create(
    model="gemini-3-pro-image-preview",
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
    )
)

# First turn: Generate initial image
response = chat.send_message("Create an infographic explaining photosynthesis")

for part in response.parts:
    if part.inline_data is not None:
        output_path = OUTPUT_DIR / "infographic_v1.png"
        part.as_image().save(output_path)
        print(f"Saved: {output_path}")

# Second turn: Modify the generated image
response = chat.send_message(
    "Translate all text to Spanish",
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        )
    )
)

for part in response.parts:
    if part.inline_data is not None:
        output_path = OUTPUT_DIR / "infographic_v2.png"
        part.as_image().save(output_path)
        print(f"Saved: {output_path}")
EOF
```

### Multi-Turn Workflow Pattern

1. **Generate** - Create initial image
2. **Review** - Check the output
3. **Refine** - Send modification request in same chat
4. **Iterate** - Continue until satisfied

## Multiple Reference Images

Combine up to 14 reference images (6 for objects, 5 for humans) to create composite images.

### Group Photo Example

```bash
uv run - << 'EOF'
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

# Output directory - Claude sets based on user request (format: NNN-short-name)
OUTPUT_DIR = Path("001-group-photo")  # <-- Claude replaces this dynamically
OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client()

# Load reference images
person1 = Image.open("person1.png")
person2 = Image.open("person2.png")
person3 = Image.open("person3.png")

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[
        "Office group photo of these people making funny faces",
        person1,
        person2,
        person3,
    ],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(aspect_ratio="5:4")
    )
)

for part in response.parts:
    if part.inline_data is not None:
        output_path = OUTPUT_DIR / "group_photo.png"
        part.as_image().save(output_path)
        print(f"Saved: {output_path}")
EOF
```

## Professional Asset Production

Use `gemini-3-pro-image-preview` for high-fidelity professional outputs.

### 4K Marketing Asset

```bash
uv run - << 'EOF'
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
from pathlib import Path
from google import genai
from google.genai import types

# Output directory - Claude sets based on user request (format: NNN-short-name)
OUTPUT_DIR = Path("001-butterfly-4k")  # <-- Claude replaces this dynamically
OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=["Da Vinci style anatomical sketch of a butterfly"],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",
            image_size="4K"
        )
    )
)

for part in response.parts:
    if part.text:
        print(part.text)
    elif part.inline_data is not None:
        output_path = OUTPUT_DIR / "butterfly_4k.png"
        part.as_image().save(output_path)
        print(f"Saved: {output_path}")
EOF
```

### Text Rendering for Infographics

The pro model excels at generating legible, stylized text for:
- Infographics and data visualizations
- Restaurant menus and marketing materials
- Diagrams with labels
- Presentations and slides

## Model Comparison

| Feature | gemini-2.5-flash-image | gemini-3-pro-image-preview |
|---------|------------------------|----------------------------|
| Speed | Fast | Slower, higher quality |
| Resolution | Up to 2K | Up to 4K |
| Text rendering | Basic | Advanced |
| Reference images | Limited | Up to 14 |
| Search grounding | No | Yes |
| Thinking process | Basic | Advanced |