from typing import Optional


class PromptBuilder:
    """Build optimized prompts for Replicate AI model"""

    # Style descriptions for each vibe
    VIBE_PROMPTS = {
        "modern": "contemporary, clean lines, sleek furniture, minimalist decor, open space",
        "minimalist": "simple, uncluttered, neutral palette, essential furniture only, zen",
        "cozy": "warm, comfortable, inviting, soft textures, ambient lighting, homey",
        "industrial": "exposed brick, metal elements, concrete, Edison bulbs, loft style, urban",
        "bohemian": "eclectic, colorful textiles, plants, vintage pieces, layered decor, artistic",
        "scandinavian": "light wood, white walls, natural materials, hygge, functional, nordic",
        "luxurious": "elegant, high-end materials, chandeliers, plush furniture, ornate, sophisticated",
        "rustic": "wood beams, natural stone, vintage furniture, farmhouse style, country charm"
    }

    # Color palette descriptions
    COLOR_PROMPTS = {
        "neutral": "beige, white, gray, cream, taupe color scheme, subtle tones",
        "warm": "terracotta, amber, rust, golden tones, warm orange and red hues",
        "cool": "blue, teal, mint, cool gray tones, calming colors",
        "earthy": "brown, olive green, terracotta, natural wood tones, earth colors",
        "pastel": "soft pink, lavender, mint, baby blue, muted colors, gentle hues",
        "bold": "vibrant colors, deep jewel tones, saturated hues, dramatic contrast"
    }

    @classmethod
    def build_prompt(
        cls,
        vibe: str,
        colors: str,
        description: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Build positive and negative prompts

        Args:
            vibe: Design vibe/style
            colors: Color palette
            description: Additional user description

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        # Build positive prompt parts
        prompt_parts = [
            f"A {vibe} interior design,",
            cls.VIBE_PROMPTS.get(vibe, "beautiful interior design"),
            f"with {cls.COLOR_PROMPTS.get(colors, 'balanced color scheme')},",
            "photorealistic, high quality, professional photography,",
            "8k resolution, detailed textures, natural lighting,",
            "architectural digest style"
        ]

        # Add user description if provided
        if description and description.strip():
            prompt_parts.insert(3, description.strip())

        positive_prompt = " ".join(prompt_parts)

        # Negative prompt for quality control
        negative_prompt = (
            "ugly, distorted, low quality, blurry, pixelated, "
            "unrealistic, artificial, cartoonish, amateur, "
            "bad proportions, deformed, disfigured, watermark, "
            "text, signature, oversaturated"
        )

        return positive_prompt, negative_prompt

    @classmethod
    def build_prompt_with_references(
        cls,
        vibe: str,
        colors: str,
        description: Optional[str] = None,
        reference_count: int = 0
    ) -> tuple[str, str]:
        """
        Build prompt considering reference images

        Args:
            vibe: Design vibe/style
            colors: Color palette
            description: Additional user description
            reference_count: Number of reference images

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        positive_prompt, negative_prompt = cls.build_prompt(vibe, colors, description)

        # Add reference image context if provided
        if reference_count > 0:
            positive_prompt += (
                f", incorporating similar elements and style from {reference_count} "
                "reference images, matching furniture style, color palette, and aesthetic"
            )

        return positive_prompt, negative_prompt
