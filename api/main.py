from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import tempfile
import os
import subprocess
import librosa
import soundfile as sf
from typing import Optional
import nemo.collections.asr as nemo_asr
from pydantic import BaseModel
from datetime import timedelta
import gc
import torch

app = FastAPI(title="Parakeet Video Subtitle API")

asr_model = None

def cleanup_memory():
    """Force garbage collection and clear GPU cache"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

@app.on_event("startup")
async def startup_event():
    global asr_model
    try:
        print("Loading Parakeet model...")
        asr_model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v3")
        print("Parakeet model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

def configure_model_for_duration(duration_seconds):
    """Configure the model based on audio duration"""
    # degrade the performance a lot for big audios, maybe slice audio would be a better approach
    duration_minutes = duration_seconds / 60
    
    if duration_minutes < 30:
        print(f"Audio {duration_minutes:.1f} min : Standard configuration")
        asr_model.change_attention_model("rel_pos_local_attn", [128, 128])
        asr_model.change_subsampling_conv_chunking_factor(1)
        return {"batch_size": 1, "use_mixed_precision": False}
    
    elif duration_minutes < 45:
        print(f"Audio {duration_minutes:.1f} min : Light memory optimization")
        asr_model.change_attention_model("rel_pos_local_attn", [128, 128])
        asr_model.change_subsampling_conv_chunking_factor(4)
        return {"batch_size": 2, "use_mixed_precision": False}
    
    elif duration_minutes < 70:
        print(f"Audio {duration_minutes:.1f} min : Medium memory optimization")
        asr_model.change_attention_model("rel_pos_local_attn", [64, 64])
        asr_model.change_subsampling_conv_chunking_factor(4)
        return {"batch_size": 1, "use_mixed_precision": False}
    
    else:
        print(f"Audio {duration_minutes:.1f} min : Aggressive memory optimization + mixed precision")
        asr_model.change_attention_model("rel_pos_local_attn", [32, 32])
        asr_model.change_subsampling_conv_chunking_factor(8)
        return {"batch_size": 1, "use_mixed_precision": True}

def extract_audio_from_video(video_path: str, output_path: str) -> bool:
    try:
        cmd = [
            'ffmpeg', '-i', video_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Audio extraction error: {e}")
        return False

def format_time(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    milliseconds = int((seconds - total_seconds) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def create_srt_content(transcription_result) -> str:
    srt_content = ""
    
    if hasattr(transcription_result, 'timestamp') and 'word' in transcription_result.timestamp:
        words = transcription_result.timestamp['word']
        segments = []
        current_segment = []
        current_start = 0
        
        for i, word_info in enumerate(words):
            if not current_segment:
                current_start = word_info['start']
            
            current_segment.append(word_info['word'])
            
            if (word_info['end'] - current_start > 7 or 
                len(current_segment) > 8 or 
                i == len(words) - 1):
                
                segment_text = ' '.join(current_segment)
                start_time = format_time(current_start)
                end_time = format_time(word_info['end'])
                
                segments.append({
                    'start': start_time,
                    'end': end_time,
                    'text': segment_text
                })
                
                current_segment = []
        
        for i, segment in enumerate(segments, 1):
            srt_content += f"{i}\n"
            srt_content += f"{segment['start']} --> {segment['end']}\n"
            srt_content += f"{segment['text']}\n\n"
    
    else:
        text = transcription_result.text if hasattr(transcription_result, 'text') else str(transcription_result)
        srt_content = "1\n00:00:00,000 --> 00:01:00,000\n" + text + "\n\n"
    
    return srt_content

@app.get("/")
async def root():
    return {"message": "Parakeet Video Subtitle API", "status": "ready" if asr_model else "loading"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if asr_model else "loading",
        "model_loaded": asr_model is not None
    }

@app.post("/cleanup")
async def force_cleanup():
    """Force memory cleanup - useful for batch processing"""
    cleanup_memory()
    return {"status": "memory cleaned"}

@app.post("/transcribe")
async def transcribe_video(file: UploadFile = File(...)):
    if asr_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav', '.flac']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Supported: {', '.join(allowed_extensions)}"
        )
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, f"input{file_extension}")
            with open(input_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            audio_path = os.path.join(temp_dir, "audio.wav")
            
            if file_extension in ['.mp3', '.wav', '.flac']:
                try:
                    y, sr = librosa.load(input_path, sr=16000, mono=True)
                    sf.write(audio_path, y, 16000)
                    del y, sr
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Audio reading error: {str(e)}")
            else:
                if not extract_audio_from_video(input_path, audio_path):
                    raise HTTPException(status_code=400, detail="Audio extraction failed")
            
            if not os.path.exists(audio_path):
                raise HTTPException(status_code=400, detail="Unable to create audio file")
            
            print("Starting transcription...")
            try:
                duration = librosa.get_duration(filename=audio_path)
                config = configure_model_for_duration(duration)
                if config["use_mixed_precision"]:
                    print("Using mixed precision for very long audio")
                    with torch.amp.autocast("cuda", enabled=True, dtype=torch.bfloat16):
                        transcription = asr_model.transcribe(
                            [audio_path], 
                            batch_size=config["batch_size"],
                            timestamps=True
                        )
                else:
                    transcription = asr_model.transcribe(
                        [audio_path], 
                        batch_size=config["batch_size"],
                        timestamps=True
                    )
            except Exception as e:
                print(f"Transcription error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

            if not transcription or len(transcription) == 0:
                raise HTTPException(status_code=400, detail="No transcription generated")
            
            result = transcription[0]
            print(f"Transcription complete. Text: {result.text[:200]}...")
            
            if hasattr(result, 'timestamp') and 'word' in result.timestamp:
                words = result.timestamp['word']
                print(f"Words with timestamps: {len(words)}")
                if words:
                    print(f"First word: {words[0]} at {words[0]['start']:.2f}s")
                    print(f"Last word: {words[-1]} at {words[-1]['end']:.2f}s")
                    print(f"Total timestamp duration: {words[-1]['end']:.2f}s")
            
            srt_content = create_srt_content(result)
            
            response_data = {
                "success": True,
                "text": result.text if hasattr(result, 'text') else str(result),
                "srt_content": srt_content,
                "filename": f"{os.path.splitext(file.filename)[0]}.srt",
                "detected_language": getattr(result, 'language', 'auto-detected')
            }
            
            if hasattr(result, 'timestamp'):
                response_data["timestamps"] = result.timestamp
            
            del transcription, result
            if file_extension in ['.mp3', '.wav', '.flac']:
                pass  # y, sr already deleted above
            
            cleanup_memory()
            
            return response_data
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
    finally:
        cleanup_memory()

@app.post("/transcribe-file")
async def transcribe_and_download(file: UploadFile = File(...)):
    result = await transcribe_video(file)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
        f.write(result["srt_content"])
        temp_srt_path = f.name
    
    def cleanup_file():
        try:
            os.unlink(temp_srt_path)
        except:
            pass
    
    return FileResponse(
        temp_srt_path,
        media_type='text/plain',
        filename=result["filename"],
        background=cleanup_file
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)