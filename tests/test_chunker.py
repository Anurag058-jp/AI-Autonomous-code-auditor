from auditor.chunker import chunk_file


def test_python_chunks_include_function_and_class(tmp_path):
    source = tmp_path / "module.py"
    source.write_text("import os\n\nclass Demo:\n    def run(self):\n        return 1\n")
    chunks = chunk_file(source, tmp_path)
    assert {chunk.name for chunk in chunks} == {"Demo", "run"}
    assert chunks[0].file_path == "module.py"
