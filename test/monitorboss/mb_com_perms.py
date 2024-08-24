import tempfile

import mb_test_resources as tr


def create_conf_file(config_content: str) -> tempfile:
    file = tempfile.NamedTemporaryFile(mode='r+t', encoding='utf-8')
    file.write(config_content)
    file.seek(0)
    return file

# def generate_get_commands():
#     for feature in ["src", "cnt"]:

def generate_get_outputs(config_content: str, attrs: [str], mons: [str], subargs: [str]):
    with create_conf_file(config_content) as conf:
        print(conf.name)
        print(conf.read())


generate_get_outputs(tr.TEST_TOML_CONTENTS, [], [], [])