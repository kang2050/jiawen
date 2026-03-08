"""
Google Veo Video Generation Client
====================================
Generate pet videos from text prompts using Google's Veo API.
Adapted from video2robot's veo_client.py.
"""

import os
import time
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console

console = Console()

# Base prompt template for pet video generation
PET_BASE_PROMPT = (
    "A realistic, high-quality video of a real pet animal in natural lighting. "
    "The camera captures the animal from multiple angles with smooth movement. "
    "The animal is clearly visible with detailed fur/feather texture. "
    "Natural environment, no text overlays. "
)


class VeoClient:
    """Google Veo API client for generating pet videos."""

    def __init__(self, config):
        self.api_key = config.api.google_api_key
        self.model = config.api.veo_model
        self.duration = config.api.video_duration
        self.resolution = config.api.video_resolution
        self.output_dir = Path(config.project_dir) / "generated_videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.api_key:
            console.print(
                "[yellow]Warning: GOOGLE_API_KEY not set. "
                "Set it in .env or pass via config.[/yellow]"
            )

    def generate(
        self,
        action: str,
        output_name: Optional[str] = None,
        pet_type: str = "dog",
        style: str = "realistic",
    ) -> Optional[str]:
        """Generate a pet video from a text description.

        Args:
            action: Description of the pet's action (e.g., "A golden retriever running in a park")
            output_name: Output filename (without extension)
            pet_type: Type of pet (dog, cat, etc.)
            style: Video style (realistic, cinematic, etc.)

        Returns:
            Path to the generated video file, or None if generation failed.
        """
        if not self.api_key:
            console.print("[red]Error: GOOGLE_API_KEY is required for Veo generation[/red]")
            return None

        # Construct full prompt
        full_prompt = f"{PET_BASE_PROMPT}\nPet type: {pet_type}. Style: {style}.\n{action}"

        console.print(f"[cyan]Generating video with Veo...[/cyan]")
        console.print(f"  Prompt: {action[:100]}...")

        try:
            # Submit generation request
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:predictLongRunning"
            headers = {"Content-Type": "application/json"}
            params = {"key": self.api_key}

            payload = {
                "instances": [{"prompt": full_prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "durationSeconds": self.duration,
                    "aspectRatio": "16:9",
                    "resolution": self.resolution,
                },
            }

            response = httpx.post(url, json=payload, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            operation = response.json()

            operation_name = operation.get("name")
            if not operation_name:
                console.print("[red]Failed to start video generation[/red]")
                return None

            # Poll for completion
            console.print(f"[cyan]Waiting for generation (operation: {operation_name})...[/cyan]")
            poll_url = f"https://generativelanguage.googleapis.com/v1beta/{operation_name}"

            for attempt in range(120):  # Max 10 minutes
                time.sleep(5)
                poll_response = httpx.get(poll_url, params=params, timeout=30)
                poll_data = poll_response.json()

                if poll_data.get("done"):
                    break

                if attempt % 6 == 0:
                    console.print(f"  Still generating... ({attempt * 5}s elapsed)")
            else:
                console.print("[red]Video generation timed out[/red]")
                return None

            # Download the generated video
            if "response" in poll_data and "predictions" in poll_data["response"]:
                video_data = poll_data["response"]["predictions"][0]
                video_url = video_data.get("videoUri") or video_data.get("uri")

                if video_url:
                    output_name = output_name or f"veo_{int(time.time())}"
                    output_path = self.output_dir / f"{output_name}.mp4"

                    video_response = httpx.get(video_url, timeout=120)
                    with open(output_path, "wb") as f:
                        f.write(video_response.content)

                    console.print(f"[green]Video saved:[/green] {output_path}")
                    return str(output_path)

            console.print("[red]No video in generation response[/red]")
            return None

        except httpx.HTTPStatusError as e:
            console.print(f"[red]API Error: {e.response.status_code} - {e.response.text}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Error generating video: {e}[/red]")
            return None


class SoraClient:
    """OpenAI Sora API client for generating pet videos."""

    def __init__(self, config):
        self.api_key = config.api.openai_api_key
        self.model = config.api.sora_model
        self.duration = config.api.video_duration
        self.output_dir = Path(config.project_dir) / "generated_videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        action: str,
        output_name: Optional[str] = None,
        pet_type: str = "dog",
    ) -> Optional[str]:
        """Generate a pet video using OpenAI Sora."""
        if not self.api_key:
            console.print("[red]Error: OPENAI_API_KEY is required for Sora generation[/red]")
            return None

        full_prompt = f"{PET_BASE_PROMPT}\nPet type: {pet_type}.\n{action}"

        console.print(f"[cyan]Generating video with Sora...[/cyan]")

        try:
            url = "https://api.openai.com/v1/videos/generations"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "duration": self.duration,
                "resolution": "720p",
            }

            response = httpx.post(url, json=payload, headers=headers, timeout=300)
            response.raise_for_status()
            result = response.json()

            video_url = result.get("data", [{}])[0].get("url")
            if video_url:
                output_name = output_name or f"sora_{int(time.time())}"
                output_path = self.output_dir / f"{output_name}.mp4"

                video_response = httpx.get(video_url, timeout=120)
                with open(output_path, "wb") as f:
                    f.write(video_response.content)

                console.print(f"[green]Video saved:[/green] {output_path}")
                return str(output_path)

            console.print("[red]No video URL in Sora response[/red]")
            return None

        except Exception as e:
            console.print(f"[red]Error generating video with Sora: {e}[/red]")
            return None
