from app.extensions import db
from app.models import Question, Quiz, QuizQuestion, Topic


def register_seed_command(app):
    @app.cli.command("seed-db")
    def seed_db():
        if Topic.query.count() > 0:
            print("Database already seeded, nothing to do.")
            return

        donanim = Topic(name="Bilgisayar Donanımı")
        guvenlik = Topic(name="İnternet ve Ağ Güvenliği")
        yazilim = Topic(name="Yazılım ve Uygulamalar")
        db.session.add_all([donanim, guvenlik, yazilim])
        db.session.flush()

        questions = [
            Question(
                topic_id=donanim.id,
                text="Aşağıdakilerden hangisi bir girdi (input) birimidir?",
                image_path=None,
                choice_a="Monitör",
                choice_b="Klavye",
                choice_c="Yazıcı",
                choice_d="Hoparlör",
                correct_choice="B",
            ),
            Question(
                topic_id=donanim.id,
                text="Bilgisayarın tüm işlemlerini yöneten ve 'beyni' olarak bilinen donanım birimi hangisidir?",
                image_path="uploads/questions/ornek-islemci.png",
                choice_a="Sabit disk",
                choice_b="RAM",
                choice_c="İşlemci (CPU)",
                choice_d="Ekran kartı",
                correct_choice="C",
            ),
            Question(
                topic_id=donanim.id,
                text="Aşağıdakilerden hangisi bir çıktı (output) birimidir?",
                image_path=None,
                choice_a="Fare",
                choice_b="Tarayıcı",
                choice_c="Mikrofon",
                choice_d="Yazıcı",
                correct_choice="D",
            ),
            Question(
                topic_id=guvenlik.id,
                text="Güçlü bir parola oluştururken aşağıdakilerden hangisine dikkat edilmelidir?",
                image_path=None,
                choice_a="Sadece küçük harf kullanmak",
                choice_b="Harf, rakam ve sembol karışımı kullanmak",
                choice_c="Doğum tarihini kullanmak",
                choice_d="İsmini parola olarak kullanmak",
                correct_choice="B",
            ),
            Question(
                topic_id=guvenlik.id,
                text="Tanımadığın birinden gelen ve kişisel bilgilerini isteyen e-postaya ne yapılmalıdır?",
                image_path=None,
                choice_a="Hemen cevap verilmeli",
                choice_b="İçindeki bağlantıya tıklanmalı",
                choice_c="Bir büyüğe danışılmalı ve silinmeli",
                choice_d="Arkadaşlara iletilmeli",
                correct_choice="C",
            ),
            Question(
                topic_id=guvenlik.id,
                text="Aşağıdakilerden hangisi güvenli internet kullanımı için doğrudur?",
                image_path=None,
                choice_a="Bilinmeyen bağlantılara tıklamak",
                choice_b="Şifreleri kimseyle paylaşmamak",
                choice_c="Her sitede aynı basit şifreyi kullanmak",
                choice_d="Kişisel fotoğrafları herkese açık paylaşmak",
                correct_choice="B",
            ),
            Question(
                topic_id=yazilim.id,
                text="Aşağıdakilerden hangisi bir işletim sistemidir?",
                image_path=None,
                choice_a="Google Chrome",
                choice_b="Microsoft Word",
                choice_c="Windows",
                choice_d="Paint",
                correct_choice="C",
            ),
            Question(
                topic_id=yazilim.id,
                text="Metin yazmak ve düzenlemek için kullanılan uygulamaya ne ad verilir?",
                image_path=None,
                choice_a="Kelime işlemci",
                choice_b="Hesap tablosu",
                choice_c="Sunu programı",
                choice_d="Web tarayıcısı",
                correct_choice="A",
            ),
            Question(
                topic_id=yazilim.id,
                text="Aşağıdakilerden hangisi bir web tarayıcısıdır?",
                image_path=None,
                choice_a="Windows",
                choice_b="Android",
                choice_c="Firefox",
                choice_d="Excel",
                correct_choice="C",
            ),
        ]
        db.session.add_all(questions)
        db.session.flush()

        quiz = Quiz(title="Örnek Quiz", slug="ornek-quiz")
        db.session.add(quiz)
        db.session.flush()

        ordered_questions = [
            questions[0],
            questions[3],
            questions[6],
            questions[1],
            questions[4],
            questions[7],
        ]
        for position, question in enumerate(ordered_questions, start=1):
            db.session.add(
                QuizQuestion(
                    quiz_id=quiz.id,
                    question_id=question.id,
                    order=position,
                )
            )

        db.session.commit()
        print("Seed data inserted.")
