import whisper
import os
from typing import List, Dict, Any
import json

class SubtitleService:
    def __init__(self):
        # Load Whisper model - using base for speed/accuracy balance
        self.model = whisper.load_model("base")
    
    def generate_subtitles(self, video_path: str, language: str = "en", timing_offset: float = 0.0) -> List[Dict[str, Any]]:
        """
        Generate subtitles for a video using Whisper.
        
        Args:
            video_path: Path to the video file
            language: Language code for transcription
            timing_offset: Offset in seconds to adjust all subtitle timings (can be negative)
            
        Returns:
            List of subtitle segments with timing and text
        """
        try:
            print(f"🎙️  Transcribing audio from: {video_path}")
            print(f"🎙️  Language: {language}")
            print(f"🎙️  Timing offset: {timing_offset}s")
            print(f"🎙️  Whisper model: {self.model.name if hasattr(self.model, 'name') else 'unknown'}")
            
            # Transcribe the audio
            result = self.model.transcribe(
                video_path,
                language=language,
                word_timestamps=True,
                verbose=False
            )
            
            print(f"🎙️  Whisper found {len(result['segments'])} segments")
            
            # Process segments into subtitle format
            subtitles = []
            for i, segment in enumerate(result["segments"]):
                # Apply timing offset
                adjusted_start = max(0, segment["start"] + timing_offset)
                adjusted_end = max(adjusted_start + 0.1, segment["end"] + timing_offset)
                
                subtitle_segment = {
                    "start": adjusted_start,
                    "end": adjusted_end,
                    "text": segment["text"].strip(),
                    "words": []
                }
                
                # Add word-level timestamps if available
                if "words" in segment:
                    print(f"   🔍 Segment {i+1} has {len(segment['words'])} words")
                    for j, word in enumerate(segment["words"]):
                        word_start = max(0, word["start"] + timing_offset)
                        word_end = max(word_start + 0.1, word["end"] + timing_offset)
                        subtitle_segment["words"].append({
                            "word": word["word"],
                            "start": word_start,
                            "end": word_end
                        })
                        # Log first few words for debugging
                        if j < 3:
                            print(f"      Word {j+1}: '{word['word'].strip()}' ({word_start:.2f}s-{word_end:.2f}s)")
                else:
                    print(f"   ❌ Segment {i+1} has NO word-level data!")
                
                subtitles.append(subtitle_segment)
                
                # Log first few segments for debugging
                if i < 3:
                    print(f"   Segment {i+1}: {adjusted_start:.2f}s-{adjusted_end:.2f}s | {segment['text'].strip()[:50]}...")
            
            return subtitles
            
        except Exception as e:
            raise Exception(f"Error generating subtitles: {str(e)}")
    
    def save_subtitle_file(self, subtitles: List[Dict[str, Any]], output_path: str, format: str = "srt") -> str:
        """
        Save subtitles to a file in the specified format.
        
        Args:
            subtitles: List of subtitle segments
            output_path: Path to save the subtitle file
            format: Subtitle format (srt, vtt, json)
            
        Returns:
            Path to the saved subtitle file
        """
        try:
            if format.lower() == "srt":
                self._save_srt(subtitles, output_path)
            elif format.lower() == "vtt":
                self._save_vtt(subtitles, output_path)
            elif format.lower() == "json":
                self._save_json(subtitles, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error saving subtitle file: {str(e)}")
    
    def _save_srt(self, subtitles: List[Dict[str, Any]], output_path: str):
        """Save subtitles in SRT format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, subtitle in enumerate(subtitles, 1):
                start_time = self._seconds_to_srt_time(subtitle["start"])
                end_time = self._seconds_to_srt_time(subtitle["end"])
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{subtitle['text']}\n\n")
    
    def _save_vtt(self, subtitles: List[Dict[str, Any]], output_path: str):
        """Save subtitles in WebVTT format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for subtitle in subtitles:
                start_time = self._seconds_to_vtt_time(subtitle["start"])
                end_time = self._seconds_to_vtt_time(subtitle["end"])
                
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{subtitle['text']}\n\n")
    
    def _save_json(self, subtitles: List[Dict[str, Any]], output_path: str):
        """Save subtitles in JSON format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, indent=2, ensure_ascii=False)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to WebVTT time format (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    
    def format_text_for_video(self, text: str, max_words_per_line: int = 4) -> str:
        """
        Format subtitle text for video display with word wrapping.
        
        Args:
            text: Original subtitle text
            max_words_per_line: Maximum words per line
            
        Returns:
            Formatted text with line breaks
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            if len(current_line) >= max_words_per_line:
                lines.append(' '.join(current_line))
                current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def analyze_timing_gaps(self, subtitles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze subtitle timing for potential synchronization issues.
        
        Args:
            subtitles: List of subtitle segments
            
        Returns:
            Dictionary with timing analysis and recommendations
        """
        if len(subtitles) < 2:
            return {"status": "insufficient_data", "recommendation": "No timing analysis possible with < 2 segments"}
        
        gaps = []
        for i in range(len(subtitles) - 1):
            current_end = subtitles[i]["end"]
            next_start = subtitles[i + 1]["start"]
            gap = next_start - current_end
            
            if gap > 0.5:  # Significant gaps
                gaps.append({
                    "after_segment": i + 1,
                    "before_segment": i + 2,
                    "gap_duration": gap,
                    "gap_start": current_end,
                    "gap_end": next_start
                })
        
        analysis = {
            "total_segments": len(subtitles),
            "significant_gaps": len(gaps),
            "largest_gap": max(gaps, key=lambda x: x["gap_duration"]) if gaps else None,
            "timing_span": subtitles[-1]["end"] - subtitles[0]["start"] if subtitles else 0
        }
        
        # Generate recommendations
        recommendations = []
        
        if gaps and len(gaps) > 0:
            largest_gap = analysis["largest_gap"]
            
            # Check if there's an unusually large gap early in the video
            early_large_gaps = [g for g in gaps if g["gap_start"] < 30 and g["gap_duration"] > 5]
            
            if early_large_gaps:
                early_gap = early_large_gaps[0]
                suggested_offset = -early_gap["gap_duration"] / 2
                recommendations.append({
                    "type": "timing_offset",
                    "severity": "high",
                    "message": f"Large {early_gap['gap_duration']:.1f}s gap detected early in video",
                    "suggested_offset": suggested_offset,
                    "reasoning": "Early large gaps often indicate subtitle timing is off from the start"
                })
            
            if largest_gap["gap_duration"] > 10:
                recommendations.append({
                    "type": "content_gap",
                    "severity": "medium", 
                    "message": f"Very large gap ({largest_gap['gap_duration']:.1f}s) suggests silence or scene change",
                    "suggested_offset": 0,
                    "reasoning": "Large gaps may be intentional silence periods"
                })
        
        # Check for very early start
        if subtitles and subtitles[0]["start"] < 1.0:
            recommendations.append({
                "type": "early_start",
                "severity": "low",
                "message": "Subtitles start very early in video",
                "suggested_offset": 1.0,
                "reasoning": "Most videos have intro/silence before speech begins"
            })
        
        analysis["recommendations"] = recommendations
        return analysis