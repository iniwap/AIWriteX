from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from src.ai_auto_wxgzh.tools.custom_tool import PublisherTool, ReadTemplateTool, AIPySearchTool
from src.ai_auto_wxgzh.utils import utils
from src.ai_auto_wxgzh.config.config import Config


@CrewBase
class AutowxGzh:
    """AutowxGzh crew"""

    agents_config = utils.get_res_path("config/agents.yaml")
    tasks_config = utils.get_res_path("config/tasks.yaml")

    def __init__(self, appid="", appsecret="", author=""):
        # 由于有多个账号循环发布，这里需要传递微信信息
        self.appid = appid
        self.appsecret = appsecret
        self.author = author

    def publisher_tool_cb(self, appid, appsecret, author):
        def callback_function(output):
            PublisherTool().run(output.raw, appid, appsecret, author)

        return callback_function

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            verbose=True,
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],
            tools=[AIPySearchTool()],
            verbose=True,
        )

    @agent
    def auditor(self) -> Agent:
        return Agent(
            config=self.agents_config["auditor"],
            verbose=True,
        )

    @agent
    def designer(self) -> Agent:
        return Agent(
            config=self.agents_config["designer"],
            verbose=True,
        )

    @agent
    def templater(self) -> Agent:
        return Agent(
            config=self.agents_config["templater"],
            tools=[ReadTemplateTool()],
            verbose=True,
        )

    @task
    def analyze_topic(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_topic"],
        )

    @task
    def write_content(self) -> Task:
        return Task(
            config=self.tasks_config["write_content"],
        )

    @task
    def audit_content(self) -> Task:
        return Task(
            config=self.tasks_config["audit_content"],
        )

    @task
    def design_content(self) -> Task:
        return Task(
            config=self.tasks_config["design_content"],
            callback=self.publisher_tool_cb(self.appid, self.appsecret, self.author),
        )

    @task
    def template_content(self) -> Task:
        return Task(
            config=self.tasks_config["template_content"],
            callback=self.publisher_tool_cb(self.appid, self.appsecret, self.author),
        )

    @crew
    def crew(self) -> Crew:
        """Creates the AutowxGzh crew"""

        config = Config.get_instance()
        no_use_agent = []
        no_use_task = []
        if config.use_template:
            no_use_agent.append("微信排版专家")
            no_use_task.append("design_content")
        else:
            no_use_agent.append("模板调整与内容填充专家")
            no_use_task.append("template_content")

        # 不开启质量审核
        if not config.need_auditor:
            no_use_agent.append("质量审核专家")
            no_use_task.append("audit_content")

        # 过滤不使用的
        self.agents = [agent for agent in self.agents if agent.role not in no_use_agent]
        self.tasks = [task for task in self.tasks if task.name not in no_use_task]

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
