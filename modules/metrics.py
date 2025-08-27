import enum
import prometheus_client

class Metrics(enum.Enum):
    
    API_RESPONSE_CODES = (
        "api_response_codes",
        "Response codes of requests made to LeetCode GraphQL API",
        prometheus_client.Counter,
        ["code"],
    )

    API_LATENCY = (
        "api_latency",
        "Latency / response time of requests made to LeetCode GraphQL API",
        prometheus_client.Summary
    )

    SIGN_LAST_UPDATED = (
        "sign_last_updated",
        "Timestamp of when the sign was last updated",
        prometheus_client.Gauge,
    )

    SIGN_UPDATE_ERROR = (
        "sign_update_error",
        "Gauge of the success of updating the sign: 0 for success and 1 for failure",
        prometheus_client.Gauge,
    )

    NULL_USERS_FOUND = (
        "null_users_found",
        "Number of times LeetCode GraphQL API returns a null / nonexistent user",
        prometheus_client.Counter,
        ["username"]
    )

    HTTP_CODE = (
        "http_code",
        "Count of each HTTP Response code",
        prometheus_client.Counter,
        ["path", "code"]
    )

    LEETCODE_API_ERROR = (
        "leetcode_api_error",
        "Gauge of the success of API calls to LeetCode: 0 for success and 1 for failure",
        prometheus_client.Gauge,
    )

    def __init__(self, title, description, prometheus_type, label=()):
        self.title = title
        self.description = description
        self.prometheus_type = prometheus_type
        self.labels = label


class MetricsHandler:
    _instance = None

    def __init__(self):
        raise RuntimeError("Call MetricsHandler.instance() instead")
    
    def init(self) -> None:
        for metric in Metrics:
            setattr(
                self,
                metric.title,
                metric.prometheus_type(
                    metric.title, metric.description, labelnames=metric.labels
                ),
            )

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls.init(cls)
        return cls._instance