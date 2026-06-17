import streamlit as st
import requests

st.set_page_config(
    page_title="AI Multi-Language Code Reviewer",
    layout="wide"
)

st.title("AI Multi-Language Code Reviewer")

# ---------------------------------
# Language Selection
# ---------------------------------

language = st.selectbox(
    "Select Programming Language",
    [
        "Python",
        "Java",
        "JavaScript",
        "C",
        "C++",
        "SQL",
        "Go",
        "Rust"
    ]
)

# ---------------------------------
# File Types
# ---------------------------------

file_types = {
    "Python": ["py"],
    "Java": ["java"],
    "JavaScript": ["js"],
    "C": ["c"],
    "C++": ["cpp", "cc", "cxx"],
    "SQL": ["sql"],
    "Go": ["go"],
    "Rust": ["rs"]
}

# ---------------------------------
# Input Section
# ---------------------------------

st.subheader("Option 1: Paste Code")

manual_code = st.text_area(
    "Paste Your Code",
    height=250
)

st.subheader("Option 2: Upload File")

uploaded_file = st.file_uploader(
    f"Upload {language} File",
    type=file_types.get(language, [])
)

code = ""

# ---------------------------------
# Validation
# ---------------------------------

if manual_code.strip() and uploaded_file is not None:

    st.error(
        "Choose only one option: Paste Code OR Upload File."
    )

    st.stop()

elif uploaded_file is not None:

    code = uploaded_file.read().decode("utf-8")

    filename = uploaded_file.name.lower()

    if filename.endswith(".py"):
        language = "Python"

    elif filename.endswith(".java"):
        language = "Java"

    elif filename.endswith(".js"):
        language = "JavaScript"

    elif filename.endswith(".cpp") or filename.endswith(".cc") or filename.endswith(".cxx"):
        language = "C++"

    elif filename.endswith(".c"):
        language = "C"

    elif filename.endswith(".sql"):
        language = "SQL"

    elif filename.endswith(".go"):
        language = "Go"

    elif filename.endswith(".rs"):
        language = "Rust"

    st.success(f"Detected Language: {language}")

    st.subheader("Uploaded Code")

    st.code(
        code,
        language=language.lower()
    )

elif manual_code.strip():

    code = manual_code

# ---------------------------------
# Review Button
# ---------------------------------

if st.button("Review Code"):

    if not code.strip():

        st.warning(
            "Please paste code or upload a file."
        )

        st.stop()

    try:

        response = requests.post(
            "https://ai-intelligent-code-reviewer.onrender.com/review",
            json={
                "code": code,
                "language": language
            },
            timeout=120
        )

        if response.status_code != 200:

            st.error(
                f"Backend Error: {response.text}"
            )

            st.stop()

        result = response.json()

        # ---------------------------------
        # Metrics
        # ---------------------------------

        issues = result.get("issues", [])

        error_count = sum(
            1 for issue in issues
            if issue.get("type") == "error"
        )

        warning_count = sum(
            1 for issue in issues
            if issue.get("type") == "warning"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Quality Score",
            result.get("score", 0)
        )

        c2.metric(
            "Errors",
            error_count
        )

        c3.metric(
            "Warnings",
            warning_count
        )

        st.subheader("Review Results")

        # ---------------------------------
        # Issues
        # ---------------------------------

        if issues:

            st.subheader("Errors Found")

            for issue in issues:

                issue_type = issue.get(
                    "type",
                    "info"
                )

                line = issue.get(
                    "line",
                    "-"
                )

                message = issue.get(
                    "message",
                    ""
                )

                if issue_type == "error":

                    st.error(
                        f"Line {line} | ERROR\n\n{message}"
                    )

                else:

                    st.warning(
                        f"Line {line} | WARNING\n\n{message}"
                    )

        # ---------------------------------
        # AI Review
        # ---------------------------------

        st.subheader("Summary")

        st.info(
            result.get(
                "summary",
                ""
            )
        )

        st.subheader("Suggested Fixes")

        st.success(
            result.get(
                "fixes",
                ""
            )
        )

        # ---------------------------------
        # Code Comparison
        # ---------------------------------

        corrected_code = result.get(
            "corrected_code",
            ""
        )

        st.subheader("Code Comparison")

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                "### Original Code"
            )

            st.code(
                code,
                language=language.lower()
            )

        with col2:

            st.markdown(
                "### Corrected Code"
            )

            st.code(
                corrected_code,
                language=language.lower()
            )

        # ---------------------------------
        # Download
        # ---------------------------------

        extension_map = {
            "Python": "py",
            "Java": "java",
            "JavaScript": "js",
            "C": "c",
            "C++": "cpp",
            "SQL": "sql",
            "Go": "go",
            "Rust": "rs"
        }

        ext = extension_map.get(
            language,
            "txt"
        )

        st.download_button(
            label="Download Fixed Code",
            data=corrected_code,
            file_name=f"fixed_code.{ext}",
            mime="text/plain"
        )

    except Exception as e:

        st.error(
            f"Application Error: {str(e)}"
        )