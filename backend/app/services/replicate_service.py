import replicate
from typing import Optional
from app.core.config import settings


class ReplicateService:
    """Service for interacting with Replicate AI API"""

    def __init__(self):
        self.api_token = settings.REPLICATE_API_TOKEN
        self.model = settings.REPLICATE_MODEL

    def transform_interior(
        self,
        image_url: str,
        prompt: str,
        negative_prompt: str,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> str:
        """
        Transform interior image using Replicate AI

        Args:
            image_url: URL of the original image
            prompt: Positive prompt describing desired result
            negative_prompt: Negative prompt for quality control
            num_inference_steps: Number of denoising steps (more = better quality but slower)
            guidance_scale: How closely to follow the prompt (7-15 is good range)
            seed: Random seed for reproducibility (optional)

        Returns:
            URL of the transformed image
        """
        input_params = {
            "image": image_url,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
        }

        if seed is not None:
            input_params["seed"] = seed

        try:
            # Run the model
            output = replicate.run(
                self.model,
                input=input_params
            )

            # Output is typically a list with one URL
            if isinstance(output, list) and len(output) > 0:
                return output[0]
            elif isinstance(output, str):
                return output
            else:
                raise ValueError(f"Unexpected output format from Replicate: {output}")

        except Exception as e:
            raise Exception(f"Replicate API error: {str(e)}")

    async def transform_interior_async(
        self,
        image_url: str,
        prompt: str,
        negative_prompt: str,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None
    ) -> str:
        """Async version of transform_interior"""
        # Replicate SDK doesn't have native async support yet
        # We'll use this in a background task with Celery
        return self.transform_interior(
            image_url,
            prompt,
            negative_prompt,
            num_inference_steps,
            guidance_scale,
            seed
        )


# Global Replicate service instance
replicate_service = ReplicateService()
