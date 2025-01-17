"""Flask application for a pastebin-like service that allows users to share text snippets."""

from datetime import datetime, timedelta, timezone
import secrets
import logging
from typing import Optional
import random

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import markdown2
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer

MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB
MAX_TITLE_LENGTH = 100
SUPPORTED_LANGUAGES = {"python", "javascript", "java", "cpp", "text"}
PASTE_EXPIRY_OPTIONS = {
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
    "1w": timedelta(weeks=1),
    "never": None,
}

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(32)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pastes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


limiter = Limiter(
    app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)

db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Paste(db.Model):
    """Model representing a text paste with syntax highlighting and markdown support."""

    id = db.Column(db.String(8), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), default="text")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)
    is_markdown = db.Column(db.Boolean, default=False)

    def generate_id(self):
        """Generate a random URL-safe ID for the paste."""
        return secrets.token_urlsafe(6)

    def format_content(self):
        """Format the paste content based on its type (markdown or code)."""
        if self.is_markdown:
            return markdown2.markdown(self.content)
        try:
            lexer = get_lexer_by_name(self.language)
        except ValueError:
            lexer = TextLexer()
        formatter = HtmlFormatter(linenos=True, cssclass="source")
        return highlight(self.content, lexer, formatter)

    def clean_content(self) -> str:
        """Sanitize and validate content before storing."""
        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("Content cannot be empty")
        if len(self.content) > MAX_CONTENT_LENGTH:
            raise ValueError(
                f"Content exceeds maximum length of {MAX_CONTENT_LENGTH} bytes"
            )
        return self.content.strip()

    def clean_title(self) -> str:
        """Sanitize and validate title."""
        if not self.title:
            return "Untitled"
        clean_title = self.title.strip()[:MAX_TITLE_LENGTH]
        return clean_title or "Untitled"

    def is_expired(self) -> bool:
        """Check if paste has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove expired pastes from database."""
        expired = cls.query.filter(
            cls.expires_at.isnot(None), cls.expires_at < datetime.utcnow()
        ).all()
        for paste in expired:
            db.session.delete(paste)
        db.session.commit()
        return len(expired)


@app.before_request
def cleanup_expired_pastes():
    """Periodically clean up expired pastes."""
    if random.random() < 0.1:  # 10% chance to run cleanup
        try:
            count = Paste.cleanup_expired()
            if count:
                logger.info(f"Cleaned up {count} expired pastes")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


@app.route("/")
def index():
    """Display the home page with recent pastes."""
    recent_pastes = Paste.query.order_by(Paste.created_at.desc()).limit(10).all()
    return render_template("index.html", recent_pastes=recent_pastes)


@app.route("/paste/new", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def new_paste():
    """Create a new paste from user input."""
    if request.method == "POST":
        try:
            content = request.form.get("content", "").strip()
            title = request.form.get("title", "").strip()
            language = request.form.get("language", "text").lower()
            expiry = request.form.get("expiry", "never")

            if language not in SUPPORTED_LANGUAGES:
                raise ValueError("Unsupported language")

            expires_at = None
            if expiry in PASTE_EXPIRY_OPTIONS:
                delta = PASTE_EXPIRY_OPTIONS[expiry]
                if delta:
                    expires_at = datetime.utcnow() + delta

            paste = Paste(
                id=secrets.token_urlsafe(6),
                title=title,
                content=content,
                language=language,
                is_markdown=request.form.get("is_markdown") == "on",
                expires_at=expires_at,
            )

            paste.content = paste.clean_content()
            paste.title = paste.clean_title()

            db.session.add(paste)
            db.session.commit()

            logger.info(f"Created new paste: {paste.id}")
            return redirect(url_for("view_paste", paste_id=paste.id))

        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            logger.error(f"Error creating paste: {e}")
            flash("An error occurred while creating the paste", "error")

        return redirect(url_for("new_paste"))

    return render_template(
        "new_paste.html",
        supported_languages=SUPPORTED_LANGUAGES,
        expiry_options=PASTE_EXPIRY_OPTIONS.keys(),
    )


@app.route("/paste/<paste_id>")
def view_paste(paste_id):
    """Display a specific paste with syntax highlighting or markdown rendering."""
    try:
        paste = Paste.query.get_or_404(paste_id)
        if paste.is_expired():
            db.session.delete(paste)
            db.session.commit()
            abort(404)

        formatted_content = paste.format_content()
        return render_template(
            "view_paste.html",
            paste=paste,
            formatted_content=formatted_content,
            css=HtmlFormatter().get_style_defs(".source"),
        )
    except Exception as e:
        logger.error(f"Error viewing paste {paste_id}: {e}")
        abort(500)


@app.route("/paste/<paste_id>/raw")
def raw_paste(paste_id):
    """Return the raw content of a paste."""
    paste = Paste.query.get_or_404(paste_id)
    return paste.content, 200, {"Content-Type": "text/plain"}


@app.route("/paste/<paste_id>/delete", methods=["POST"])
def delete_paste(paste_id):
    """Delete a paste from the database."""
    paste = Paste.query.get_or_404(paste_id)
    db.session.delete(paste)
    db.session.commit()
    flash("Paste deleted successfully", "success")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return render_template("500.html"), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
