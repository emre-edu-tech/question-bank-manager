from datetime import datetime

from app.extensions import db


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

    questions = db.relationship("Question", back_populates="topic")


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topic.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String, nullable=True)
    choice_a = db.Column(db.String, nullable=False)
    choice_b = db.Column(db.String, nullable=False)
    choice_c = db.Column(db.String, nullable=False)
    choice_d = db.Column(db.String, nullable=False)
    correct_choice = db.Column(
        db.Enum("A", "B", "C", "D", name="correct_choice_enum"),
        nullable=False,
    )

    topic = db.relationship("Topic", back_populates="questions")


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    slug = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quiz_questions = db.relationship(
        "QuizQuestion", back_populates="quiz", order_by="QuizQuestion.order"
    )


class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    question_id = db.Column(
        db.Integer, db.ForeignKey("question.id"), nullable=False
    )
    order = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("quiz_id", "question_id"),
    )

    quiz = db.relationship("Quiz", back_populates="quiz_questions")
    question = db.relationship("Question")


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), nullable=False)
    class_code = db.Column(db.String(20), nullable=False)
    total_xp = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('nickname', 'class_code', name='uq_student_nickname_class'),
    )


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=0)
    total_questions = db.Column(db.Integer, nullable=False)
    xp_earned = db.Column(db.Integer, nullable=False, default=0)
    lives_remaining = db.Column(db.Integer, nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    student = db.relationship('Student', backref='attempts')
    quiz = db.relationship('Quiz', backref='attempts')


class QuizAttemptAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_choice = db.Column(db.String(1), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    time_taken_seconds = db.Column(db.Float, nullable=True)
    xp_awarded = db.Column(db.Integer, nullable=False, default=0)

    attempt = db.relationship('QuizAttempt', backref='answers')
    question = db.relationship('Question')


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)


class StudentBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='student_badges')
    badge = db.relationship('Badge')

    __table_args__ = (db.UniqueConstraint('student_id', 'badge_id', name='uq_student_badge'),)
