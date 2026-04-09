from server.graders import grade_task, grade_task_1, grade_task_2, grade_task_3

GRADERS = {
    "task_1_easy": grade_task_1,
    "task_2_medium": grade_task_2,
    "task_3_hard": grade_task_3,
}

__all__ = ["GRADERS", "grade_task", "grade_task_1", "grade_task_2", "grade_task_3"]
