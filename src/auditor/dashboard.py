import streamlit as st
# Streamlit executes this file as a script, outside the ``auditor`` package.
# An absolute import therefore works both for ``audit dashboard`` and direct runs.
from auditor.service import AuditService


def main():
    st.set_page_config(page_title="Code Auditor", layout="wide")
    st.title("Zero-Cost AI Code Auditor")
    source = st.text_input("Local repository path or public GitHub URL")
    if st.button("Run audit", type="primary") and source:
        with st.spinner("Scanning repository..."):
            try:
                st.session_state.result = AuditService().scan(source)
            except Exception as error:
                st.error(str(error))
    result = st.session_state.get("result")
    if not result:
        return
    st.caption(f"Scan {result['scan_id']} · {result['files_scanned']} files · {len(result['findings'])} findings")
    severity = st.multiselect("Severity", ["critical", "high", "medium", "low"], default=["critical", "high", "medium", "low"])
    for finding in [f for f in result["findings"] if f["severity"] in severity]:
        with st.expander(f"[{finding['severity'].upper()}] {finding['title']} — {finding['file_path']}:{finding['start_line']}"):
            st.code(finding["evidence"])
            st.write(finding["description"])
            st.info(finding["remediation"])
            left, right = st.columns(2)
            for action, column in [("fix", left), ("test", right)]:
                if column.button(f"Generate {action}", key=f"{action}-{finding['id']}"):
                    try:
                        st.code(AuditService().generate(result["scan_id"], finding["id"], action), language="diff" if action == "fix" else "python")
                    except Exception as error:
                        st.warning(str(error))


if __name__ == "__main__":
    main()
