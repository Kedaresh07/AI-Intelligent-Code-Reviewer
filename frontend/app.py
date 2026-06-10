import streamlit as st
import requests

st.set_page_config(
    page_title="AI Intelligent Code Reviewer",
    layout="wide"
)

st.title("AI Intelligent Code Reviewer")

# ---------------------------
# Input Section
# ---------------------------

st.subheader("Option 1: Paste Code")

manual_code = st.text_area(
    "Paste Your Python Code",
    height=200
)

st.subheader("Option 2: Upload Python File")

uploaded_file = st.file_uploader(
    "Upload Python File",
    type=["py"]
)

code = ""

if manual_code.strip() and uploaded_file is not None:

    st.error(
        "Choose only one option: Paste Code OR Upload File."
    )

    st.stop()

elif uploaded_file is not None:

    code = uploaded_file.read().decode("utf-8")

    st.subheader("Uploaded Code")
    st.code(code, language="python")

elif manual_code.strip():

    code = manual_code

# ---------------------------
# Review Button
# ---------------------------

if st.button("Review Code"):

    if not code.strip():
        st.warning("Please paste code or upload a Python file.")
        st.stop()

    try:

        response = requests.post(
            "http://127.0.0.1:8000/review",
            json={"code": code}
        )

        if response.status_code != 200:
            st.error(f"Backend Error: {response.text}")
            st.stop()

        result = response.json()

        # ---------------------------
        # Score
        # ---------------------------

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

        c1.metric("Quality Score", result.get("score", 0))
        c2.metric("Errors", error_count)
        c3.metric("Warnings", warning_count)




        st.subheader("Review Results")

        st.success(
            f"Code Quality Score: {result.get('score', 0)} / 10"
        )

        # ---------------------------
        # Issues
        # ---------------------------

        issues = result.get("issues", [])

        if issues:

            st.subheader("Errors Found")

            for issue in issues:

                issue_type = issue.get("type", "")
                line = issue.get("line", "")
                message = issue.get("message", "")

                st.error(
                    f"Line {line} | {issue_type.upper()}\n\n{message}"
                )

        else:
            st.success("No major issues detected.")

        # ---------------------------
        # AI Review
        # ---------------------------

        st.subheader("Summary")
        st.info(result.get("summary", ""))

        st.subheader("Suggested Fixes")
        st.warning(result.get("fixes", ""))

        corrected_code = result.get("corrected_code", "")

        st.subheader("Code Comparison")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Original Code")
            st.code(code, language="python")

        with col2:
            st.markdown("### Corrected Code")
            st.code(corrected_code, language="python")

        st.download_button(
            label="Download Fixed Code",
            data=corrected_code,
            file_name="fixed_code.py",
            mime="text/plain"
        )

    except Exception as e:
        st.error(f"Application Error: {str(e)}")