try:
    from email_review_env.graders import grade_task_1 as grade
except ModuleNotFoundError:
    from server.graders import grade_task_1 as grade

__all__ = ["grade"]
