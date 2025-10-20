
from typing import Dict, Any, List, Optional
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import io
from psycopg2.extras import Json

from agent.database.db_manager import DatabaseManager
from agent.database.db_singleton import get_db

db = get_db()

def _is_title_slide(slide_data: Dict[str, Any]) -> bool:
    """Intelligently detect if a slide should be a title slide."""
    points = slide_data.get("points", [])

    # A title slide has no bullet points or very few (for subtitle)
    if len(points) == 0:
        return True
    elif len(points) == 1:
        # Check if it's a simple string (subtitle) or a nested bullet
        point = points[0]
        if isinstance(point, str) and len(point) < 100:
            return True

    return False


def _calculate_font_size(bullet_count: int) -> int:
    """Dynamically calculate font size based on bullet count."""
    if bullet_count <= 5:
        return 20  # Normal size
    elif bullet_count <= 8:
        return 18  # Slightly smaller
    else:
        return 16  # Compact


def _flatten_bullets(points: List[Any]) -> int:
    """Count total bullets including nested ones for font sizing."""
    count = 0
    for point in points:
        if isinstance(point, dict):
            count += 1  # Main point
            count += len(point.get("sub_points", []))  # Sub-points
        else:
            count += 1
    return count


def _create_presentation_bytes(slides: List[Dict[str, Any]]) -> bytes:
    """Create a PowerPoint presentation using proper layouts and bullet formatting."""
    prs = Presentation()

    # Set presentation dimensions to widescreen (16:9)
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)

    # Define Granite brand color scheme
    GRANITE_BLUE = RGBColor(41, 128, 185)      # Primary accent blue
    DARK_TEXT = RGBColor(44, 62, 80)           # Dark gray for text
    LIGHT_BG = RGBColor(245, 247, 250)         # Light background
    ACCENT_LIGHT = RGBColor(174, 214, 241)     # Light blue accent

    total_slides = len(slides)

    for idx, slide_data in enumerate(slides):
        title = slide_data.get("title", "Untitled")
        points = slide_data.get("points", [])
        is_title = idx == 0 and _is_title_slide(slide_data)

        if is_title:
            # Create a completely custom title slide with no template constraints
            slide_layout = prs.slide_layouts[6]  # Blank layout
            slide = prs.slides.add_slide(slide_layout)

            # Adaptive font size based on title length - be aggressive to avoid wrapping
            title_length = len(title)
            if title_length < 15:
                title_font_size = 54
            elif title_length < 25:
                title_font_size = 44
            elif title_length < 35:
                title_font_size = 36
            elif title_length < 50:
                title_font_size = 28
            else:
                title_font_size = 24

            # Calculate vertical center: slide height is 5.625 inches
            vertical_center = 5.625 / 2  # 2.8125 inches
            title_height_estimate = 1.5
            title_top = vertical_center - (title_height_estimate / 2)  # Center vertically

            # Title text box - CENTERED
            title_box = slide.shapes.add_textbox(
                Inches(0.5),
                Inches(title_top),
                Inches(9),
                Inches(title_height_estimate)
            )
            title_frame = title_box.text_frame
            title_frame.word_wrap = True
            title_frame.vertical_anchor = 1  # Middle vertical anchor

            p = title_frame.paragraphs[0]
            p.text = title
            p.font.size = Pt(title_font_size)
            p.font.bold = True
            p.font.color.rgb = GRANITE_BLUE
            p.alignment = PP_ALIGN.CENTER

            # Subtitle - below title
            if len(points) == 1:
                subtitle_text = str(points[0])
                subtitle_box = slide.shapes.add_textbox(
                    Inches(0.5),
                    Inches(title_top + title_height_estimate + 0.3),
                    Inches(9),
                    Inches(0.8)
                )
                subtitle_frame = subtitle_box.text_frame
                subtitle_frame.word_wrap = True

                sub_p = subtitle_frame.paragraphs[0]
                sub_p.text = subtitle_text
                sub_p.font.size = Pt(28)
                sub_p.font.color.rgb = DARK_TEXT
                sub_p.alignment = PP_ALIGN.CENTER

            # Granite branding at bottom
            brand_box = slide.shapes.add_textbox(
                Inches(0.5),
                Inches(5.1),
                Inches(9),
                Inches(0.4)
            )
            brand_frame = brand_box.text_frame

            brand_p = brand_frame.paragraphs[0]
            brand_p.text = "Granite"
            brand_p.font.size = Pt(16)
            brand_p.font.color.rgb = ACCENT_LIGHT
            brand_p.alignment = PP_ALIGN.CENTER

        else:
            # Use title and content layout
            slide_layout = prs.slide_layouts[1]  # Title and content layout
            slide = prs.slides.add_slide(slide_layout)

            # Set title
            title_shape = slide.shapes.title
            title_shape.text = title
            title_frame = title_shape.text_frame
            title_frame.word_wrap = True

            for paragraph in title_frame.paragraphs:
                paragraph.font.size = Pt(44)
                paragraph.font.bold = True
                paragraph.font.color.rgb = GRANITE_BLUE
                paragraph.alignment = PP_ALIGN.LEFT

            # Set content (bullets)
            if len(slide.placeholders) > 1 and points:
                body_shape = slide.placeholders[1]
                text_frame = body_shape.text_frame
                text_frame.clear()
                text_frame.word_wrap = True

                # Calculate font size based on bullet count
                total_bullets = _flatten_bullets(points)
                font_size = _calculate_font_size(total_bullets)

                for point_idx, point in enumerate(points):
                    if isinstance(point, dict):
                        # Main bullet with nested structure
                        if point_idx == 0:
                            p = text_frame.paragraphs[0]
                        else:
                            p = text_frame.add_paragraph()

                        p.text = point.get("text", "")
                        p.level = 0
                        p.font.size = Pt(font_size)
                        p.font.bold = True
                        p.font.color.rgb = GRANITE_BLUE

                        # Add sub-points
                        sub_points = point.get("sub_points", [])
                        for sub_point in sub_points:
                            sub_p = text_frame.add_paragraph()
                            sub_p.text = sub_point
                            sub_p.level = 1
                            sub_p.font.size = Pt(font_size - 2)
                            sub_p.font.color.rgb = DARK_TEXT

                    else:
                        # Simple string bullet
                        if point_idx == 0:
                            p = text_frame.paragraphs[0]
                        else:
                            p = text_frame.add_paragraph()

                        p.text = point
                        p.level = 0
                        p.font.size = Pt(font_size)
                        p.font.color.rgb = DARK_TEXT

            # Add footer with slide number
            if len(slide.placeholders) > 2:
                # Try to use footer placeholder if available
                try:
                    footer = slide.placeholders[2]
                    footer.text = f"Slide {idx}/{total_slides}"
                except:
                    pass

    # Save to bytes
    f = io.BytesIO()
    prs.save(f)
    f.seek(0)
    return f.read()

def _validate_presentation_structure(slides: List[Dict[str, Any]]) -> tuple[bool, str]:
    """
    Validate presentation structure and provide feedback.

    Returns:
        Tuple of (is_valid, message)
    """
    warnings = []

    for idx, slide in enumerate(slides):
        points = slide.get("points", [])
        total_bullets = _flatten_bullets(points)

        # Check for too many bullets
        if total_bullets > 8:
            warnings.append(f"Slide {idx + 1} has {total_bullets} bullet points. Consider splitting into 2 slides (ideal: 3-7 bullets)")

        # Validate structure format
        for point_idx, point in enumerate(points):
            if isinstance(point, dict):
                # Check required fields
                if "text" not in point:
                    return False, f"Slide {idx + 1}, bullet {point_idx + 1}: Nested bullet missing 'text' field"

                # Check sub-points format
                sub_points = point.get("sub_points", [])
                if sub_points and not isinstance(sub_points, list):
                    return False, f"Slide {idx + 1}, bullet {point_idx + 1}: 'sub_points' must be a list"

            elif not isinstance(point, str):
                return False, f"Slide {idx + 1}, bullet {point_idx + 1}: Point must be string or nested object with 'text' field"

    # Return validation result with warnings
    if warnings:
        warning_text = "\n".join(["⚠️ " + w for w in warnings])
        return True, f"Presentation is valid but has suggestions:\n{warning_text}\nProceeding with save..."
    else:
        return True, "✅ Presentation structure is optimal!"


def tool_save_presentation_structure(
    presentation_title: str,
    slides: List[Dict[str, Any]],
    presentation_description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Saves the structured presentation outline to the database.

    Args:
        presentation_title: The title of the presentation (must be unique).
        slides: A list of slides, where each slide is a dictionary with "title" and "points".
        presentation_description: Optional description of the presentation.

    Returns:
        A dictionary with the success status.
    """
    try:
        # Validate structure
        is_valid, validation_msg = _validate_presentation_structure(slides)
        if not is_valid:
            return {
                "success": False,
                "error": "Invalid presentation structure",
                "message": validation_msg
            }

        # Check if presentation already exists
        existing = db.get_presentation_by_title(presentation_title)

        structure = {"slides": slides}

        if existing:
            # Update existing presentation
            with db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE presentations
                        SET presentation_structure = %s,
                            presentation_description = %s
                        WHERE presentation_title = %s
                    """, (Json(structure), presentation_description, presentation_title))
                    conn.commit()
            return {
                "success": True,
                "message": f"Presentation '{presentation_title}' updated successfully with {len(slides)} slides\n{validation_msg}"
            }
        else:
            # Create new presentation
            with db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO presentations
                        (presentation_title, presentation_description, presentation_structure)
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """, (presentation_title, presentation_description, Json(structure)))
                    conn.commit()
                    pres_id = cursor.fetchone()[0]
            return {
                "success": True,
                "message": f"Presentation '{presentation_title}' saved successfully with {len(slides)} slides\n{validation_msg}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to save presentation structure: {str(e)}"
        }

def tool_generate_presentation_from_db(
    rfp_id: str,
    file_name: str
) -> Dict[str, Any]:
    """
    Generates a PowerPoint presentation from a structured outline stored in the database.

    Args:
        rfp_id: The ID of the RFP associated with the presentation.
        file_name: The desired name for the generated PowerPoint file.

    Returns:
        A dictionary with the success status and the presentation content as bytes.
    """
    try:
        presentation_data = db.get_presentation_structure(rfp_id)
        if not presentation_data or "slides" not in presentation_data:
            return {"success": False, "error": "No presentation structure found", "message": f"No presentation structure found for RFP: {rfp_id}"}

        slides = presentation_data["slides"]
        ppt_bytes = _create_presentation_bytes(slides)

        return {
            "success": True,
            "file_name": file_name,
            "content": ppt_bytes,
            "message": f"Successfully generated presentation {file_name} from DB for RFP: {rfp_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate presentation from DB: {str(e)}"
        }
