from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text,Integer
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

connections.create_connection(hosts=["115.28.82.133"])

html_strip = analyzer('html_strip',
    tokenizer="standard",
    filter=["standard", "lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)

class Comment(InnerObjectWrapper):
    def age(self):
        return datetime.now() - self.created_at


#弥补es_dsl代码缺陷
class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer("ik_max_word",filter=['lowercase'])


class Question(DocType):
    url = Keyword()
    topics = Text(analyzer="ik_max_word")
    title = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")
    comments_num = Keyword()
    follow_and_watch = Keyword()
    created_time = Keyword()
    updated_time = Keyword()

    class Meta:
        index="zhihu"
        doc_type="questions"


class Answer(DocType):
    url = Keyword()
    question_id = Keyword()
    author_id = Keyword()
    content = Text(analyzer="ik_max_word")
    vote_up_num = Keyword()
    comments_num = Keyword()
    created_time = Keyword()
    updated_time = Keyword()

    class Meta:
        index="zhihu"
        doc_type="answers"


class Post(DocType):
    #es_dsl的代码Competion貌似有缺陷不能直接写参数
    suggest = Completion(analyzer=ik_analyzer, search_analyzer=ik_analyzer)

    url = Keyword()
    title = Text(analyzer="ik_max_word")
    post_at = Date()
    like_num = Integer()
    fav_num = Integer()
    comments_num = Integer()
    post_thumb = Keyword()
    thumb_path = Keyword()
    content = Text(analyzer="ik_max_word")
    tags = Text(analyzer="ik_max_word")

    class Meta:
        index="jobbole"
        doc_type="articles"


class Job(DocType):
    #es_dsl的代码Competion貌似有缺陷不能直接写参数
    suggest = Completion(analyzer=ik_analyzer, search_analyzer=ik_analyzer)

    url = Keyword()
    title = Text(analyzer="ik_max_word")
    salary = Keyword()
    city = Keyword()
    work_years = Keyword()
    degree_need = Keyword()
    job_type = Keyword()
    job_addr = Keyword()
    publish_time = Keyword()
    tags = Text(analyzer="ik_max_word")
    job_advantage = Keyword()
    job_desc = Keyword()
    company_url = Keyword()
    company_name = Keyword()

    class Meta:
        index="lagou"
        doc_type="jobs"

if __name__ == "__main__":
    Post.init()
    Job.init()