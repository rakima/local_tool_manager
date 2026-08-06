from local_tool_manager.models import Tool


def command_tool(name="Sample", category="開発"):
    return Tool(name=name, entry_type="command", command="python")


def test_create_get_and_delete(repository):
    created = repository.create(command_tool())
    assert created.id is not None
    assert repository.get(created.id).name == "Sample"

    repository.delete(created.id)

    assert repository.list() == []


def test_update(repository):
    created = repository.create(command_tool())
    created.name = "Updated"

    updated = repository.update(created)

    assert updated.name == "Updated"


def test_search_name_description_and_category_case_insensitive(repository):
    tool = command_tool("Build Helper")
    tool.description = "Deploy LOCAL app"
    tool.category = "Development"
    repository.create(tool)
    repository.create(command_tool("Other", "業務"))

    assert len(repository.list(search="helper")) == 1
    assert len(repository.list(search="local")) == 1
    assert len(repository.list(search="development")) == 1


def test_reorders_tools_and_appends_new_tool(repository):
    first = repository.create(command_tool("First"))
    second = repository.create(command_tool("Second"))
    third = repository.create(command_tool("Third"))

    repository.reorder([third.id, first.id, second.id])
    added = repository.create(command_tool("Added"))

    assert [tool.id for tool in repository.list()] == [
        third.id,
        first.id,
        second.id,
        added.id,
    ]

