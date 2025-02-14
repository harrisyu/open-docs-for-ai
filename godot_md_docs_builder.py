# D:\local_docs\godot-docs-html-3.6
# pip install beautifulsoup4 html2text
# python godot_md_docs_builder.py --combine D:\local_docs\godot-docs-html-master\classes out\godot-latest-classes.md --workers 12 --ignore-file godot-latest-classes-ignore.txt
# python godot_md_docs_builder.py --combine D:\local_docs\godot-docs-html-3.6\classes out\godot-3.6-classes.md --workers 12 --ignore-file godot-3.6-classes-ignore.txt
# python godot_md_docs_builder.py D:\local_docs\godot-docs-html-master\ out\godot-latest-docs\ --workers 12 --clean --ignore-file godot-latest-docs-ignore.txt
# python godot_md_docs_builder.py D:\local_docs\godot-docs-html-3.6\ out\godot-3.6-docs\ --workers 12 --clean --ignore-file godot-3.6-docs-ignore.txt

import os
import argparse
from bs4 import BeautifulSoup
import html2text
from concurrent.futures import ProcessPoolExecutor, as_completed
import re
import fnmatch
import shutil  # Add this import at the top


def convert_html_to_markdown(html_file, base_path):
    """Convert a single HTML file to Markdown with proper formatting"""
    print(f"Processing {html_file}")
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Remove unwanted elements
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()

    # Remove tutorials section
    for section in soup.find_all(
        "section", {"class": "classref-introduction-group", "id": "tutorials"}
    ):
        section.decompose()

    # Remove C# tabs and panels
    for tab_container in soup.find_all(class_="sphinx-tabs docutils container"):
        # Find and remove C# buttons and panels
        for button in tab_container.find_all("button", class_="sphinx-tabs-tab"):
            if "C#" in button.get_text():
                # Find and remove corresponding panel using aria-controls
                panel_id = button.get("aria-controls")
                if panel_id:
                    panel = tab_container.find("div", id=panel_id)
                    if panel:
                        panel.decompose()
                button.decompose()

    # Remove navigation div
    for nav in soup.find_all("div", attrs={"role": "navigation"}):
        nav.decompose()

    # Remove icon elements
    for icon in soup.find_all(class_=["fa", "icon", "headerlink"]):
        icon.decompose()

    # Remove the "latest notice" admonition
    for notice in soup.find_all(class_="admonition attention latest-notice"):
        notice.decompose()

    # Remove the "rst-versions" div
    for versions in soup.find_all(class_="rst-versions"):
        versions.decompose()

    # Find main content area
    main_content = soup.find("div", {"class": "content"}) or soup.body

    # Remove H1 tags from content to prevent duplication
    for h1 in main_content.find_all("h1"):
        h1.decompose()

    # Configure markdown converter to preserve code formatting
    converter = html2text.HTML2Text()
    converter.bypass_tables = False
    # Add code block prefix identifier
    converter.protect_links = True
    converter.mark_code = True  # Preserve code block markers
    converter.body_width = 120  # Wider lines for method signatures
    converter.emphasis_mark = ""  # Disable italic/bold
    converter.strong_mark = ""
    converter.code_mark = "`"  # Preserve backticks for code
    converter.wrap_tables = False  # Keep table formatting
    converter.ul_item_mark = "-"  # Clear list formatting

    # Generate markdown content
    rel_path = os.path.relpath(html_file, base_path)
    markdown = f"<!-- FILE: {rel_path} -->\n"

    # Clean title text - remove DEV prefix and documentation suffixes
    title = soup.title.string if soup.title else ""
    title = re.sub(r"^\(DEV\)\s*", "", title)  # Remove (DEV) prefix
    title = re.sub(r"\s—\sGodot Engine.*$", "", title)  # Remove suffix
    title = re.sub(r"\s-\sGodot Engine.*$", "", title)  # Alternative suffix format
    markdown += f"## {title}\n\n" if title else "## Documentation\n\n"

    # Increment header levels in main content
    for i in range(6, 0, -1):  # Process from h6 to h1 to avoid conflicts
        for header in main_content.find_all(f"h{i}"):
            header.name = f"h{i+1}"  # Add 2 levels to each header

    content = converter.handle(str(main_content))

    # Combine all parts before processing
    full_content = f"{markdown}{content}"

    # Post-process cleanup
    full_content = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)", r"\1", full_content
    )  # Remove links but keep text
    full_content = re.sub(
        r":\s*(\w+)", r": \1", full_content
    )  # Ensure space after colon
    full_content = re.sub(r"{#.*?}", "", full_content)
    full_content = re.sub(r"\bclass_", "", full_content)
    full_content = re.sub(r"{.*?}", "", full_content)
    full_content = re.sub(r"\n{3,}", "\n\n", full_content)

    # Enhanced cleanup for method/property signatures
    full_content = re.sub(
        r"(\*\*.*?\*\*)(\()", r"\1 \2", full_content
    )  # Space before params
    full_content = re.sub(r":(\w)", r": \1", full_content)  # Space after colon in types
    full_content = re.sub(r"(\w)(=)", r"\1 \2", full_content)  # Space around equals

    # Add empty header row to tables and reorder rows
    full_content = re.sub(
        r"(?m)^([^\n]*\|[^\n]*)\n((?:---\s*\|\s*)*---)\s*\n",  # Match first row and separator line
        lambda m: (
            # Create empty header with matching columns
            "|"
            + " | ".join(["  " for _ in m.group(2).split("|")])
            + "|\n"
            + m.group(2)
            + "\n"  # Separator line
            + m.group(1)
            + "\n"  # Original first row moved after separator
        ),
        full_content,
    )

    full_content = re.sub(r"(\S)\|(\S)", r"\1 | \2", full_content)  # Table spacing
    full_content = re.sub(r"(\w)<(\w)", r"\1< \2", full_content)  # Generics spacing
    full_content = re.sub(r"(\w)>(\w)", r"\1> \2", full_content)

    # Preserve type annotations
    full_content = re.sub(r"(\w+):\s*([A-Z][\w\.]+)", r"\1: \2", full_content)

    # Post-process cleanup for special characters
    full_content = re.sub(
        r"[\uf0c1\uf002\uf07c\uf078\uf077]", "", full_content
    )  # Remove common FontAwesome chars
    full_content = re.sub(
        r"[\ue000-\uf8ff]", "", full_content
    )  # Remove Unicode private area chars
    full_content = re.sub(r"🔗", "", full_content)  # Remove link emoji

    # Convert [code] tags to markdown code blocks with GDScript language tag
    full_content = re.sub(
        r"\[code\]([\s\S]*?)\[/code\]",  # Capture everything including whitespace
        lambda m: (
            "```GDScript"
            + m.group(1)  # Keep all original content including whitespace
            + "```"
        ),
        full_content,
        flags=re.DOTALL,
    )

    # Remove backticks from non-code-block text while preserving code blocks
    full_content = re.sub(
        r"(?<!`)(?<!```)`([^`\n]+)`(?!`)(?!```)",  # Match single backticks, avoid triple backticks and code blocks
        r"\1",  # Replace with just the text
        full_content,
    )

    # Remove the final separator when writing individual files
    if not hasattr(convert_html_to_markdown, "combine_output"):
        return full_content

    return full_content + "\n\n---\n\n"


def ensure_directory_exists(file_path):
    """Ensure the directory for the given file path exists"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def process_file(html_file, input_dir, output_path):
    """Process a single HTML file and save it as markdown"""
    rel_path = os.path.relpath(html_file, input_dir)

    # Get the filename and remove class_ prefix if present
    filename = os.path.basename(rel_path)
    if filename.startswith("class_"):
        filename = filename[6:]  # Remove "class_" (length is 6)

    # Create output path with same structure but .md extension and without class_ prefix
    output_file = os.path.join(
        output_path, os.path.dirname(rel_path), os.path.splitext(filename)[0] + ".md"
    )

    # Ensure output directory exists
    ensure_directory_exists(output_file)

    # Convert and write individual file
    content = convert_html_to_markdown(html_file, input_dir)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    return rel_path


def process_html_docs_folder(
    input_dir,
    output_path,
    max_workers=8,
    page_limit=-1,
    ignore_patterns=None,
    combine=False,
):
    """Process HTML files using multiple processes"""
    html_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(input_dir)
        for f in files
        if f.endswith(".html")
    ]

    # Sort files by their relative paths to maintain folder order
    html_files.sort(key=lambda x: os.path.relpath(x, input_dir).replace("\\", "/"))

    # Filter out ignored files first
    if ignore_patterns:
        filtered_files = []
        ignored_files = []
        for file_path in html_files:
            rel_path = os.path.relpath(file_path, input_dir)
            rel_path_unix = rel_path.replace("\\", "/")
            matches = False
            for pattern in ignore_patterns:
                if pattern.startswith("*/"):
                    pattern = "*" + pattern
                if fnmatch.fnmatch(rel_path_unix, pattern):
                    matches = True
                    break

            if not matches:
                filtered_files.append(file_path)
            else:
                ignored_files.append(rel_path_unix)

        if ignored_files:
            print(f"\nIgnored {len(ignored_files)} files:")
            for file in ignored_files:  # Show all ignored files
                print(f"  {file}")
            print()

        html_files = filtered_files

    # Apply page limit after filtering
    if page_limit > 0:
        html_files = html_files[:page_limit]
        print(f"Processing first {page_limit} pages after filtering")

    # Set combine mode flag
    convert_html_to_markdown.combine_output = combine

    if combine:
        # Group files by directory for combined output
        grouped_files = {}
        for file_path in html_files:
            rel_path = os.path.relpath(file_path, input_dir).replace("\\", "/")
            directory = os.path.dirname(rel_path)
            if not directory:
                directory = "root"
            if directory not in grouped_files:
                grouped_files[directory] = []
            grouped_files[directory].append(file_path)

        # Original behavior - combine all into one file
        with ProcessPoolExecutor(max_workers=max_workers) as executor, open(
            output_path, "w", encoding="utf-8"
        ) as md_file:
            # Process files by directory to maintain structure
            for directory, files in grouped_files.items():
                # Add directory header
                if directory != "root":
                    header = f"\n\n# {directory.replace('/', ' / ')}\n\n"
                    md_file.write(header)

                # Process current directory's files
                chunk_size = max(1, len(files) // (max_workers * 2))
                futures = []
                for i in range(0, len(files), chunk_size):
                    chunk = files[i : i + chunk_size]
                    futures.append(executor.submit(process_chunk, chunk, input_dir))

                # Collect and write results in order
                for future in as_completed(futures):
                    results = future.result()
                    md_file.write("\n".join(filter(None, results)))

    else:
        # Process files in parallel
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Create futures with partial function to include input_dir and output_path
            futures = [
                executor.submit(process_file, f, input_dir, output_path)
                for f in html_files
            ]

            # Wait for completion and show progress
            for future in as_completed(futures):
                try:
                    rel_path = future.result()
                    print(f"Processed: {rel_path}")
                except Exception as e:
                    print(f"Error processing file: {e}")


def process_chunk(files, base_path):
    """Process a chunk of files in a single process"""
    return [convert_html_to_markdown(f, base_path) for f in files]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Multithreaded HTML to Markdown Converter"
    )
    parser.add_argument("input_dir", help="Path to documentation HTML folder")
    parser.add_argument("output_path", help="Path to output markdown file or directory")
    parser.add_argument(
        "--workers", type=int, default=8, help="Number of worker processes (default: 8)"
    )
    parser.add_argument(
        "--page-limit",
        type=int,
        default=-1,
        help="Limit number of pages to process (for testing), -1=all (default: -1)",
    )
    parser.add_argument(
        "--ignore-file", help="Path to file containing list of files/patterns to ignore"
    )
    parser.add_argument(
        "--combine",
        action="store_true",
        help="Combine all output into a single markdown file (default: separate files)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean the output directory before processing (default: False)",
    )
    args = parser.parse_args()

    # Read ignore patterns if specified
    ignore_patterns = []
    if args.ignore_file:
        with open(args.ignore_file, "r", encoding="utf-8") as f:
            ignore_patterns = [line.strip() for line in f if line.strip()]

    # Clean output if requested
    if args.clean:
        if args.combine:
            if os.path.exists(args.output_path):
                os.remove(args.output_path)
                print(f"Cleaned output file: {args.output_path}")
        else:
            if os.path.exists(args.output_path):
                shutil.rmtree(args.output_path)
                print(f"Cleaned output directory: {args.output_path}")

    # Create output directory if not combining and directory doesn't exist
    if not args.combine and not os.path.exists(args.output_path):
        os.makedirs(args.output_path)

    process_html_docs_folder(
        args.input_dir,
        args.output_path,
        args.workers,
        args.page_limit,
        ignore_patterns,
        args.combine,
    )

    print(f"Conversion complete! Output saved to {args.output_path}")


""" 
# Ignore file samples:

# Ignore all files in classes/ directory
classes/*

# Exclude specific HTML files
development/features/*.html

# Skip index files
*/index.html

# Ignore test files
*_test.html

# Exclude files starting with underscore
_*.html

# Ignore specific subdirectory structure
demos/3d/*/source/* 
"""
