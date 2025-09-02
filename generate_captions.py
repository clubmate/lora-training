#!/usr/bin/env python3
"""
LORA Training Caption Generation Script

This script generates captions for images using the Florence-2 model.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForCausalLM
import logging
from typing import List, Dict, Any

def setup_logging(log_level: str = "INFO") -> None:
    """Sets up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(message)s'
    )

def load_config(config_path: str) -> Dict[str, Any]:
    """Loads configuration from a YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error loading configuration: {e}")
        sys.exit(1)

def get_image_files(directory: Path, supported_formats: List[str]) -> List[Path]:
    """Get all image files from a directory."""
    image_files = []
    for fmt in supported_formats:
        image_files.extend(directory.glob(f"*{fmt}"))
    return image_files

def generate_caption(model, processor, image_path: Path, device: str, caption_config: Dict[str, Any]) -> str:
    """Generates a caption for a single image using Florence-2."""
    try:
        image = Image.open(image_path).convert("RGB")
        
        # Get Florence-2 captioning prompt from config
        prompt = caption_config.get("prompt", "<MORE_DETAILED_CAPTION>")
        
        # Determine torch_dtype
        torch_dtype = torch.float16 if device == "cuda" else torch.float32
        
        # Process the image
        inputs = processor(text=prompt, images=image, return_tensors="pt")
        
        # Move inputs to device with proper dtype - check for None first
        inputs_to_device = {}
        for k, v in inputs.items():
            if v is not None:
                if hasattr(v, 'dtype') and v.dtype.is_floating_point:
                    inputs_to_device[k] = v.to(device, torch_dtype)
                else:
                    inputs_to_device[k] = v.to(device)
            else:
                inputs_to_device[k] = v
        
        # Generate caption - use simple greedy search to avoid beam search issues
        generated_ids = model.generate(
            input_ids=inputs_to_device["input_ids"],
            pixel_values=inputs_to_device["pixel_values"],
            max_new_tokens=caption_config.get("max_new_tokens", 1024),
            do_sample=caption_config.get("do_sample", False),
            use_cache=caption_config.get("use_cache", False)  # Disable cache to avoid past_key_values issues
        )
        
        # Decode the generated text
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        
        # Parse the output using Florence-2's post-processing
        parsed_answer = processor.post_process_generation(
            generated_text, 
            task=prompt, 
            image_size=(image.width, image.height)
        )
        
        # Extract the caption text
        caption = parsed_answer.get(prompt, "")
        if isinstance(caption, str):
            processed_caption = caption.strip()
        elif isinstance(caption, list) and len(caption) > 0:
            processed_caption = caption[0].strip()
        else:
            return "Unable to generate caption"
        
        # Remove unwanted phrases from the beginning
        remove_phrases = caption_config.get("remove_phrases", [])
        for phrase in remove_phrases:
            if processed_caption.lower().startswith(phrase.lower()):
                # Remove the phrase and clean up the result
                processed_caption = processed_caption[len(phrase):].strip()
                # Capitalize the first letter if needed
                if processed_caption and processed_caption[0].islower():
                    processed_caption = processed_caption[0].upper() + processed_caption[1:]
                break
        
        return processed_caption
            
    except Exception as e:
        logging.error(f"Error in generate_caption: {e}")
        return f"Error: {str(e)}"

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate captions for LORA training images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_captions.py datasets/aigarasch/512x512
  python generate_captions.py datasets/mymodel/1024x1024
  python generate_captions.py /path/to/images --config custom_config.yaml
  python generate_captions.py datasets/aigarasch/512x512 --log-level DEBUG

The script generates .txt caption files for all images in the specified directory.
        """
    )
    
    parser.add_argument(
        'input_directory',
        help='Path to the directory containing images to caption (required)'
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration file (default: config.yaml).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO).",
    )
    args = parser.parse_args()
    setup_logging(args.log_level)

    # Check if input directory exists
    if not os.path.exists(args.input_directory):
        logging.error(f"Input directory does not exist: {args.input_directory}")
        sys.exit(1)

    config = load_config(args.config)
    caption_config = config.get("caption", {})
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Using device: {device}")

    # Load Florence-2 model from config
    model_id = caption_config.get("model_id", "microsoft/Florence-2-large")
    prompt = caption_config.get("prompt", "<MORE_DETAILED_CAPTION>")
    logging.info(f"Loading Florence-2 model: {model_id}")
    logging.info(f"Using caption prompt: {prompt}")
    
    # Determine torch_dtype
    torch_dtype = torch.float16 if device == "cuda" else torch.float32
    
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        trust_remote_code=True,
        device_map="auto" if device == "cuda" else None,
        attn_implementation="eager"  # Force eager attention to avoid SDPA issues
    ).to(device)
    
    if device != "cuda":
        model = model.to(device)

    # Process the specified directory
    input_dir = Path(args.input_directory)
    supported_formats = config.get("supported_formats", [".png", ".jpg", ".jpeg"])
    
    logging.info(f"Processing directory: {input_dir}")
    
    if not input_dir.exists():
        logging.error(f"Directory does not exist: {input_dir}")
        sys.exit(1)
    
    if not input_dir.is_dir():
        logging.error(f"Path is not a directory: {input_dir}")
        sys.exit(1)

    image_files = get_image_files(input_dir, supported_formats)
    
    if not image_files:
        logging.warning("No image files found in the specified directory!")
        return
    
    total_files = len(image_files)
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    logging.info(f"Found {total_files} image files")
    
    for i, image_path in enumerate(image_files, 1):
        caption_path = image_path.with_suffix(".txt")
        
        if caption_path.exists():
            logging.info(f"({i}/{total_files}) Caption already exists for {image_path.name}, skipping.")
            skipped_count += 1
            continue

        logging.info(f"({i}/{total_files}) Generating caption for {image_path.name}...")
        try:
            caption = generate_caption(model, processor, image_path, device, caption_config)
            if not caption.startswith("Error:"):
                with open(caption_path, "w", encoding="utf-8") as f:
                    f.write(caption)
                logging.info(f"{caption}")
                processed_count += 1
            else:
                logging.error(f"  -> Failed: {caption}")
                error_count += 1
        except Exception as e:
            logging.error(f"  -> Failed to generate caption for {image_path.name}: {e}")
            error_count += 1
    
    # Summary
    logging.info(f"\nCaption generation completed!")
    logging.info(f"Processed: {processed_count}/{total_files}")
    logging.info(f"Skipped (already exist): {skipped_count}")
    if error_count > 0:
        logging.warning(f"Errors: {error_count}")

if __name__ == "__main__":
    main()
