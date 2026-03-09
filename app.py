import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full", layout_file="layouts/app.grid.json")


@app.cell
def imports():
    import marimo as mo
    import os
    import pandas as pd
    from processor import process_document
    from pathlib import Path

    return Path, mo, os, pd, process_document


@app.cell
def app_header(mo):
    mo.md("""
    # 📑 Document Understanding
    """)
    return


@app.cell
def upload_button(mo):
    upload_button = mo.ui.file(label="Upload", multiple=False)
    upload_area = mo.ui.file(
        label="Upload a document to process", multiple=False, kind="area"
    )
    # mo.vstack([upload_button, upload_area])
    upload_button
    return upload_area, upload_button


@app.cell
def upload_result(mo, os, upload_area, upload_button):
    upload_result_ui = mo.md("")

    upload = upload_button if upload_button.value else upload_area

    if upload.value:
        os.makedirs("outputs", exist_ok=True)
        _file_info = upload.value[0]
        _save_path = os.path.join("outputs", _file_info.name)
        with open(_save_path, "wb") as _f_out:
            _f_out.write(_file_info.contents)
        upload_result_ui = mo.md(
            f"✅ Successfully uploaded `{_file_info.name}` to `outputs/`"
        )
    upload_result_ui
    return (upload,)


@app.cell
def doc_browser(mo, os, upload):
    # Refresh when an upload happens
    _ = upload

    os.makedirs("outputs", exist_ok=True)

    doc_browser = mo.ui.file_browser(
        initial_path="outputs",
        filetypes=[".pdf", ".html", ".txt"],
        restrict_navigation=True,
        multiple=False,
        label="Select document to process:",
    )
    doc_browser
    return (doc_browser,)


@app.cell
def doc_path(doc_browser):
    doc_path = str(doc_browser.path(0)) if doc_browser.value else None
    return (doc_path,)


@app.cell
def doc_status(doc_path, mo, os):
    is_valid = doc_path and not doc_path.endswith("_annotated.pdf")

    is_processed = False
    if is_valid:
        _base_name = os.path.splitext(os.path.basename(doc_path))[0]
        _json_path = os.path.normpath(
            os.path.join("outputs", _base_name + ".json")
        )
        is_processed = os.path.exists(_json_path)

    process_btn = mo.ui.button(
        label="Reprocess Document (overwrite)"
        if is_processed
        else "Process Selected Document",
        kind="danger" if is_processed else "success",
        disabled=not is_valid,
        value=0,
        on_click=lambda value: value + 1,
    )

    if not doc_path:
        msg = "Please select a document."
    elif not is_valid:
        msg = "⚠️ Selected document is an annotated version. Please select the original document."
    elif is_processed:
        msg = f"⚠️ `{doc_path}` has already been processed. Are you sure you want to process it again?"
    else:
        msg = f"Ready to process `{doc_path}`."

    _layout = mo.vstack([mo.md(msg), process_btn])
    _layout
    return (process_btn,)


@app.cell
async def process_status(doc_path, mo, process_btn, process_document):
    process_status = mo.md("")

    if process_btn.value and doc_path and not doc_path.endswith("_annotated.pdf"):
        with mo.status.spinner(f"Processing {doc_path}..."):
            with mo.redirect_stdout(), mo.redirect_stderr():
                await process_document(input_file=doc_path)
        process_status = mo.md(f"✅ Finished processing `{doc_path}`")
    process_status
    return


@app.cell
def pdf_view(Path, doc_path, mo, os, process_btn):
    # Depend on process_btn to refresh when clicked
    _ = process_btn

    _pdf_view = mo.md("No annotated PDF found.")

    if doc_path:
        _base_name = os.path.splitext(os.path.basename(doc_path))[0]
        _annotated_path = os.path.normpath(
            os.path.join("outputs", _base_name + "_annotated.pdf")
        )

        if os.path.exists(_annotated_path):
            # with open(_annotated_path, "rb") as _f_pdf:
            # _pdf_data = _f_pdf.read()
            _p = Path(_annotated_path)
            _pdf_view = mo.pdf(src=_p, width="100%", height="600px")

    _pdf_layout = mo.vstack([mo.md("### Annotated PDF Visualization"), _pdf_view])
    _pdf_layout
    return


@app.cell
def df_view(doc_path, mo, os, pd, process_btn):
    _ = process_btn

    _df_view = mo.md("No Extracted Data (Parquet) found.")
    _parquet_path = ""

    if doc_path:
        _base_name = os.path.splitext(os.path.basename(doc_path))[0]
        _parquet_path = os.path.normpath(
            os.path.join("outputs", _base_name + ".parquet")
        )

        if os.path.exists(_parquet_path):
            try:
                _df = pd.read_parquet(_parquet_path)
                # _df_view = mo.ui.dataframe(_df)
                _df_view = mo.ui.table(_df)
            except Exception as _e:
                _df_view = mo.md(f"Error reading parquet file: {_e}")

    _df_layout = mo.vstack(
        [
            mo.md("### Extracted DataFrame"),
            mo.md(f"File: {_parquet_path}"),
            _df_view,
        ]
    )
    _df_layout
    return


if __name__ == "__main__":
    app.run()
