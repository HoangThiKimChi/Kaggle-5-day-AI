# language: vi
Feature: Hướng dẫn viết Two-Part Question Essay
  Là một học sinh Việt Nam level A2-B1 đang ôn IELTS Writing Task 2
  Tôi muốn được hướng dẫn nhận diện và viết đúng Two-Part Question essay
  Để không bỏ sót câu hỏi nào và cân bằng 2 body paragraphs

  Background:
    Given học sinh có level "A2" hoặc "B1"
    And agent đã load references từ "two_part_question_brainstorm.md" và "essay_templates.md"

  # ---------------------------------------------------------------------------
  # CLASSIFY
  # ---------------------------------------------------------------------------

  Rule: Agent phải nhận diện đúng Two-Part Question qua 2 dấu hỏi riêng biệt

    Scenario Outline: Nhận diện Two-Part Question essay
      Given học sinh cung cấp đề bài "<prompt>"
      When agent gọi classify_essay_type
      Then kết quả phải là essay_type = "two_part_question"
      And agent xác định "Câu hỏi 1" là "<q1>" và "Câu hỏi 2" là "<q2>"
      And agent cảnh báo: "Phải trả lời ĐỦ CẢ HAI câu hỏi — đây là lỗi mất điểm phổ biến nhất"

      Examples:
        | prompt                                                                                                                  | q1                      | q2                                |
        | More people live alone. What are the reasons? Is this positive or negative?                                             | reasons for living alone | positive or negative development  |
        | Young people spend more time on mobile phones. Why is this? What effects does it have?                                 | why use more phones      | effects on people and society     |
        | Many choose gap year before university. Do you think this is positive or negative? Why?                                | positive or negative     | reasons for your view             |
        | Social media has negative impact. To what extent do you agree? What can be done to minimise effects?                   | extent of agreement      | solutions to minimise effects     |
        | Nowadays many choose to be self-employed. Why might this be? What are the disadvantages?                               | why self-employed        | what are the disadvantages        |

    Scenario: Đếm số dấu hỏi trong đề để nhận diện Two-Part Question
      Given học sinh không chắc đây là dạng đề gì
      When agent phân tích đề bài
      Then agent đếm số câu hỏi (dấu ?) trong đề
      And nếu có 2 câu hỏi riêng biệt → agent classify là "two_part_question"
      And agent highlight 2 câu hỏi bằng màu/ký hiệu khác nhau

    Scenario: Phân biệt Two-Part Question với Problem-Solution
      Given đề bài có "Why is this?" và "What can be done?"
      When agent classify
      Then agent phân tích: nếu cả 2 câu xoay quanh 1 vấn đề duy nhất → "problem_solution"
      And nếu câu 2 hỏi opinion/effect (không phải solution) → "two_part_question"

  # ---------------------------------------------------------------------------
  # BRAINSTORM
  # ---------------------------------------------------------------------------

  Rule: Agent phải hướng dẫn brainstorm riêng cho từng câu hỏi

    Scenario: Hướng dẫn 7 câu hỏi brainstorm cho Two-Part Question
      Given học sinh cần brainstorm Two-Part Question essay
      When agent hướng dẫn
      Then agent dẫn qua 7 câu hỏi:
        | # | câu hỏi                                               |
        | 1 | Topic words là gì?                                     |
        | 2 | Câu hỏi 1 hỏi gì? (reasons/why/causes?)               |
        | 3 | Ít nhất 2 reasons/points cho câu hỏi 1 là gì?         |
        | 4 | Ví dụ cụ thể nào cho câu hỏi 1?                       |
        | 5 | Câu hỏi 2 hỏi gì? (opinion/effects/solutions?)        |
        | 6 | Ít nhất 2 points cho câu hỏi 2 là gì?                 |
        | 7 | Ví dụ cụ thể nào cho câu hỏi 2?                       |

    Scenario: Xác định variant của câu hỏi 2
      Given học sinh đã xác định được 2 câu hỏi trong đề
      When agent hướng dẫn brainstorm câu hỏi 2
      Then agent xác định variant và hướng dẫn tương ứng:
        | variant câu hỏi 2              | hướng dẫn                                     |
        | "Is this positive or negative?" | Chọn 1 phía, đưa ra 2 lý do                  |
        | "What effects does this have?"  | Liệt kê 2 effects (positive + negative ok)    |
        | "What can be done?"             | Đề xuất 2 solutions cụ thể (ai làm, làm gì)  |

    Scenario Outline: Gợi ý ideas theo topic thường gặp
      Given topic của Two-Part Question essay là "<topic>"
      When agent gợi ý ideas
      Then agent cung cấp ít nhất 2 ideas cho Q1 "<q1_type>"
      And agent cung cấp ít nhất 2 ideas cho Q2 "<q2_type>"

      Examples:
        | topic               | q1_type | q2_type            |
        | living alone        | reasons | positive/negative  |
        | mobile phones youth | reasons | effects            |
        | gap year            | reasons | positive/negative  |
        | immigration         | reasons | effects on country |
        | social media harm   | opinion | solutions          |

  # ---------------------------------------------------------------------------
  # INTRODUCTION
  # ---------------------------------------------------------------------------

  Rule: Introduction phải nêu rõ essay sẽ trả lời CẢ HAI câu hỏi

    Scenario: Hướng dẫn viết Introduction cho Two-Part Question essay
      Given học sinh đã xác định được 2 câu hỏi
      When agent hướng dẫn viết introduction
      Then agent cung cấp template:
        """
        [Paraphrase đề]. This essay will [explore the main reasons behind
        this trend / examine why this is happening] before [arguing that /
        considering / outlining] [câu trả lời tóm tắt cho câu hỏi 2].
        """
      And agent nhấn mạnh: introduction phải signal rõ essay sẽ trả lời 2 câu hỏi

    Scenario: Phát hiện introduction chỉ đề cập 1 câu hỏi
      Given học sinh viết introduction chỉ nhắc đến câu hỏi 1
      When agent review
      Then agent chỉ ra thiếu sót
      And agent yêu cầu bổ sung tín hiệu cho câu hỏi 2 vào introduction

  # ---------------------------------------------------------------------------
  # BODY PARAGRAPHS
  # ---------------------------------------------------------------------------

  Rule: Body 1 = Q1, Body 2 = Q2 — mỗi body chỉ trả lời 1 câu hỏi

    Scenario: Hướng dẫn cấu trúc Body 1 (trả lời Q1 — thường là Why/Reasons)
      Given câu hỏi 1 là "Why" hoặc "What are the reasons"
      When agent hướng dẫn body 1
      Then agent cung cấp template:
        """
        There are several reasons why [trend/phenomenon] has become so widespread.
        Firstly, [reason 1]. This is because [explanation].
        Furthermore, [reason 2], which means that [effect].
        For example, [specific evidence].
        """
      And agent cung cấp useful phrases:
        | phrase                                        |
        | There are several reasons why...              |
        | One key reason for this is...                 |
        | Another significant factor is...              |
        | This can partly be explained by...            |

    Scenario: Hướng dẫn cấu trúc Body 2 khi Q2 = "Positive or negative?"
      Given câu hỏi 2 là "Is this a positive or negative development?"
      When agent hướng dẫn body 2
      Then agent yêu cầu học sinh chọn 1 phía rõ ràng trước
      And agent cung cấp template:
        """
        [I believe this is largely a positive/negative development.]
        [Reason 1: explanation + example.]
        [Reason 2: explanation + example.]
        [Brief acknowledgement of the other side if balanced.]
        """

    Scenario: Hướng dẫn cấu trúc Body 2 khi Q2 = "What effects?"
      Given câu hỏi 2 là "What effects does this have?"
      When agent hướng dẫn body 2
      Then agent cung cấp template:
        """
        This trend has several significant effects on individuals and society.
        [Effect 1: explanation + example.]
        [Effect 2: explanation + example.]
        """

    Scenario: Hướng dẫn cấu trúc Body 2 khi Q2 = "What can be done?"
      Given câu hỏi 2 là "What can be done to minimise the effects?"
      When agent hướng dẫn body 2
      Then agent cung cấp template:
        """
        Several measures could be taken to address this issue.
        [Solution 1: who + what + why effective.]
        [Solution 2: who + what + why effective.]
        """

    Scenario: Phát hiện lỗi dồn cả 2 câu hỏi vào 1 body paragraph
      Given học sinh viết 1 body paragraph trả lời cả Q1 lẫn Q2
      When agent review
      Then agent phát hiện lỗi dồn 2 câu hỏi
      And agent giải thích: "Mỗi câu hỏi = 1 body paragraph riêng biệt"
      And agent hướng dẫn chia lại thành 2 paragraphs

    Scenario: Kiểm tra body paragraphs cân bằng
      Given học sinh đã viết 2 body paragraphs
      When agent review
      Then agent kiểm tra độ dài 2 paragraphs có tương đương không
      And nếu lệch đáng kể → agent gợi ý mở rộng paragraph ngắn hơn

  # ---------------------------------------------------------------------------
  # CONCLUSION
  # ---------------------------------------------------------------------------

  Rule: Conclusion phải tóm tắt cả 2 câu trả lời

    Scenario: Hướng dẫn viết Conclusion cho Two-Part Question essay
      Given học sinh đã viết xong 2 body paragraphs
      When agent hướng dẫn conclusion
      Then agent cung cấp template:
        """
        In conclusion, [trend] is primarily driven by [summary of Q1 answer].
        [Summary of Q2 answer — positive/negative/effects/solutions].
        """
      And agent nhắc: conclusion phải phản ánh CẢ HAI câu hỏi, không chỉ 1

    Scenario: Phát hiện conclusion chỉ tóm tắt 1 câu hỏi
      Given học sinh viết conclusion chỉ đề cập Q1
      When agent review
      Then agent chỉ ra thiếu sót
      And agent yêu cầu thêm tóm tắt cho Q2

  # ---------------------------------------------------------------------------
  # COMMON ERRORS
  # ---------------------------------------------------------------------------

  Scenario Outline: Phát hiện lỗi thường gặp trong Two-Part Question essay
    Given học sinh mắc lỗi "<loi>"
    When agent review bài
    Then agent chỉ ra lỗi và hướng dẫn sửa bằng tiếng Việt

    Examples:
      | loi                                                              |
      | Chỉ trả lời 1 trong 2 câu hỏi                                    |
      | Dồn cả 2 câu hỏi vào 1 body paragraph                            |
      | Body 2 ngắn hơn body 1 đáng kể                                   |
      | Conclusion chỉ tóm tắt 1 câu hỏi                                 |
      | Introduction không nêu rõ sẽ trả lời 2 câu hỏi                   |
      | Nhầm dạng Two-Part với Problem-Solution                           |

  # ---------------------------------------------------------------------------
  # CHECKLIST
  # ---------------------------------------------------------------------------

  Scenario: Cung cấp checklist Two-Part Question trước khi nộp bài
    Given học sinh đã viết xong Two-Part Question essay
    When học sinh yêu cầu kiểm tra
    Then agent chạy checklist:
      | mục                                                                  | pass/fail |
      | Xác định được 2 câu hỏi riêng biệt trong đề                         | ?         |
      | Introduction signal rõ sẽ trả lời cả 2 câu hỏi                      | ?         |
      | Body 1 CHỈ trả lời câu hỏi 1                                        | ?         |
      | Body 2 CHỈ trả lời câu hỏi 2                                        | ?         |
      | Mỗi body có ít nhất 2 points + examples                              | ?         |
      | 2 body paragraphs cân bằng độ dài                                    | ?         |
      | Conclusion tóm tắt CẢ 2 câu hỏi                                     | ?         |
      | Style formal, đủ 250 từ                                              | ?         |
    And agent báo cáo pass/fail và gợi ý cải thiện
