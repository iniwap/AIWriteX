from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from src.ai_auto_wxgzh.tools.custom_tool import PublisherTool, ReadTemplateTool
from src.ai_auto_wxgzh.utils import utils


@CrewBase
class AutowxGzh:
    """AutowxGzh crew"""

    agents_config = utils.get_res_path("config/agents.yaml")
    tasks_config = utils.get_res_path("config/tasks.yaml")

    def __init__(self, use_template=False, need_auditor=False):
        self.use_template = use_template  # 是否使用本地模板
        self.need_auditor = need_auditor  # 是否开启质量审核，关闭降低token消耗

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

    @agent
    def publisher(self) -> Agent:
        return Agent(
            config=self.agents_config["publisher"],
            tools=[PublisherTool()],
            function_calling_llm=True,  # 纯本地工具
            verbose=False,  # 纯本地工具，不要输出
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
            output_file="tmp_article.html",
        )

    @task
    def template_content(self) -> Task:
        return Task(
            config=self.tasks_config["template_content"],
            output_file="tmp_article.html",
        )

    @task
    def publish_task(self) -> Task:
        return Task(
            config=self.tasks_config["publish_task"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the AutowxGzh crew"""

        no_use_agent = []
        no_use_task = []
        if self.use_template:
            no_use_agent.append("微信排版专家")
            no_use_task.append("design_content")
        else:
            no_use_agent.append("模板调整与内容填充专家")
            no_use_task.append("template_content")

        # 不开启质量审核
        if not self.need_auditor:
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
