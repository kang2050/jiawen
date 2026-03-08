"""
Video2Pet Web Interface
========================
Gradio-based web UI for the Video2Pet pipeline.
Provides an intuitive interface for uploading videos and generating 3D pet assets.
"""

import os
import tempfile
from pathlib import Path

import gradio as gr


def create_app(config=None):
    """Create Gradio web application."""

    if config is None:
        from video2pet.config import Video2PetConfig
        config = Video2PetConfig()

    def process_video(
        video_file,
        pet_type,
        breed,
        prompt_text,
        use_ai_generation,
        fast_mode,
        skip_rigging,
        progress=gr.Progress(),
    ):
        """Process uploaded video through the pipeline."""
        from video2pet.pipeline import Video2PetPipeline

        # Create temp output directory
        output_dir = tempfile.mkdtemp(prefix="video2pet_")
        config.project_dir = output_dir

        if fast_mode:
            config.reconstruction.gs_iterations = 5000
            config.video.max_frames = 100

        pipeline = Video2PetPipeline(config)

        progress(0.1, desc="Initializing pipeline...")

        try:
            if use_ai_generation and prompt_text:
                progress(0.2, desc="Generating video from prompt...")
                results = pipeline.run(
                    prompt=prompt_text,
                    pet_type=pet_type,
                    breed=breed,
                    skip_rigging=skip_rigging,
                )
            elif video_file:
                progress(0.2, desc="Processing video...")
                results = pipeline.run(
                    video_path=video_file,
                    pet_type=pet_type,
                    breed=breed,
                    skip_rigging=skip_rigging,
                )
            else:
                return None, "Please upload a video or enter a prompt.", None

            progress(1.0, desc="Complete!")

            # Collect outputs
            status_text = "Pipeline completed successfully!\n\n"

            if "timing" in results:
                status_text += "Timing:\n"
                for stage, duration in results["timing"].items():
                    status_text += f"  {stage}: {duration:.1f}s\n"

            # Get exported files
            export_files = []
            if "exports" in results:
                for fmt, path in results["exports"].items():
                    if path and Path(path).exists():
                        export_files.append(path)

            # Get mesh for 3D viewer
            mesh_path = None
            if "mesh" in results and "obj_path" in results["mesh"]:
                mesh_path = results["mesh"]["obj_path"]

            return (
                mesh_path,
                status_text,
                export_files[0] if export_files else None,
            )

        except Exception as e:
            return None, f"Error: {str(e)}", None

    # Build Gradio interface
    with gr.Blocks(title="佳文 — 宠物数字生命") as app:
        gr.Markdown(
            """
            # 🐾 佳文 — 宠物数字生命

            上传一段宠物视频，或输入文字描述让 AI 生成视频，自动创建高精度的 3D 宠物数字孪生资产。

            **技术栈**: 姿态估计 → 3D Gaussian Splatting → 网格提取 → 自动骨骼绑定 → GLB/USDZ 导出
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 输入")

                with gr.Tab("上传视频"):
                    video_input = gr.Video(label="宠物视频", sources=["upload"])

                with gr.Tab("AI生成"):
                    use_ai = gr.Checkbox(label="使用AI生成视频", value=False)
                    prompt_input = gr.Textbox(
                        label="视频描述",
                        placeholder="例如: A golden retriever playing fetch in a sunny park",
                        lines=3,
                    )

                with gr.Row():
                    pet_type_input = gr.Dropdown(
                        choices=["dog", "cat", "rabbit", "bird"],
                        value="dog",
                        label="宠物类型",
                    )
                    breed_input = gr.Dropdown(
                        choices=[
                            "generic", "golden_retriever", "corgi",
                            "german_shepherd", "chihuahua",
                            "cat_generic", "persian_cat", "siamese_cat",
                        ],
                        value="generic",
                        label="品种",
                    )

                with gr.Row():
                    fast_mode = gr.Checkbox(label="快速模式", value=True)
                    skip_rig = gr.Checkbox(label="跳过骨骼绑定", value=False)

                run_btn = gr.Button("🚀 开始处理", variant="primary", size="lg")

            with gr.Column(scale=1):
                gr.Markdown("### 输出")
                status_output = gr.Textbox(label="处理状态", lines=10, interactive=False)
                model_output = gr.Model3D(label="3D 预览")
                file_output = gr.File(label="下载资产")

        run_btn.click(
            fn=process_video,
            inputs=[video_input, pet_type_input, breed_input, prompt_input, use_ai, fast_mode, skip_rig],
            outputs=[model_output, status_output, file_output],
        )

        gr.Markdown(
            """
            ---
            **Video2Pet** | 基于 [video2robot](https://github.com/AIM-Intelligence/video2robot) 开源项目
            | MIT License | Optimized for Apple Silicon (M2 Max)
            """
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=8000,
        share=False,
        theme=gr.themes.Soft(primary_hue="teal", secondary_hue="orange"),
    )
