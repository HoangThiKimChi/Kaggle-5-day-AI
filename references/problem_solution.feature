# language: vi
Feature: Hướng dẫn viết Problem-Solution Essay
  Là một học sinh Việt Nam level A2-B1 đang ôn IELTS Writing Task 2
  Tôi muốn được hướng dẫn viết Problem-Solution essay đúng cấu trúc
  Để solutions được match với causes và đủ cụ thể

  Background:
    Given học sinh có level "A2" hoặc "B1"
    And agent đã load references từ "problem_solution_brainstorm.md" và "essay_templates.md"

  # ---------------------------------------------------------------------------
  # CLASSIFY
  # ---------------------------------------------------------------------------

  Rule: Agent phải nhận diện đúng Problem-Solution essay và xác định variant

    Scenario Outline: Nhận diện Problem-Solution essay qua keywords
      Given học sinh cung cấp đề bài "<prompt>"
      When agent gọi classify_essay_type
      Then kết quả phải là essay_type = "problem_solution"
      And agent xác định variant "<variant>"
      And agent giải thích bằng tiếng Việt cần trả lời những gì

      Examples:
        | prompt                                                                                          | variant           |
        | Traffic congestion is a major problem. What are the causes and what measures could be taken?    | cause + solution  |
        | Many people leave rural areas. What problems does this cause and what solutions can you suggest? | problem + solution|
        | Work stress is increasing. What are the reasons? How could this problem be tackled?             | cause + solution  |
        | Obesity is a growing problem. What are the causes? What solutions can you propose?              | cause + solution  |

    Scenario: Phân biệt Problem-Solution với Two-Part Question
      Given đề bài có 2 câu hỏi rõ ràng nhưng 1 câu hỏi về cause và 1 về solution
      When agent classify
      Then agent phải đánh giá: nếu cả 2 câu hỏi đều xoay quanh 1 vấn đề → "problem_solution"
      And nếu 2 câu hỏi về 2 chủ đề khác nhau hoàn toàn → "two_part_question"

    Scenario: Hướng dẫn chọn variant phù hợp cho A2-B1
      Given học sinh xác định được essay_type là "problem_solution"
      When agent tư vấn structure
      Then agent khuyên dùng Variant A hoặc B (2 body paragraphs)
      And agent giải thích Variant C (3 body) quá phức tạp cho A2-B1
      And agent trình bày bảng so sánh:
        | variant   | body 1         | body 2       | phù hợp    |
        | Variant A | Problems       | Solutions    | A2-B1 ✅   |
        | Variant B | Causes         | Solutions    | A2-B1 ✅   |
        | Variant C | Causes/Effects/Solutions 3 paragraph riêng | B2+ ❌ |

  # ---------------------------------------------------------------------------
  # BRAINSTORM
  # ---------------------------------------------------------------------------

  Rule: Agent phải hướng dẫn match solutions với causes

    Scenario: Hướng dẫn 7 câu hỏi brainstorm
      Given học sinh cần brainstorm Problem-Solution essay
      When agent hướng dẫn brainstorm
      Then agent dẫn qua 7 câu hỏi:
        | # | câu hỏi                                                    |
        | 1 | Topic words là gì? Task words là gì?                        |
        | 2 | Vấn đề chính được đề cập là gì?                             |
        | 3 | Nguyên nhân/vấn đề 1 là gì?                                 |
        | 4 | Nguyên nhân/vấn đề 2 là gì?                                 |
        | 5 | Giải pháp nào cho nguyên nhân/vấn đề 1?                     |
        | 6 | Giải pháp nào cho nguyên nhân/vấn đề 2?                     |
        | 7 | Ai chịu trách nhiệm thực hiện? (cá nhân/chính phủ/doanh nghiệp) |

    Scenario: Hướng dẫn nguyên tắc match solutions với causes
      Given học sinh đã brainstorm xong causes
      When agent hướng dẫn tìm solutions
      Then agent giải thích nguyên tắc: "Mỗi solution phải match với 1 cause tương ứng"
      And agent cung cấp ví dụ bảng cause-solution:
        | cause                           | solution tương ứng                   |
        | Thiếu giao thông công cộng      | Phát triển metro / bus nhanh         |
        | Tăng sở hữu xe cá nhân          | Đánh thuế cao hơn vào xe cá nhân    |
      And agent nhắc: "Solution quá chung chung sẽ không được điểm cao"

    Scenario Outline: Gợi ý causes và solutions theo topic
      Given topic của Problem-Solution essay là "<topic>"
      When agent gợi ý ideas
      Then agent cung cấp ít nhất 2 causes/problems cho "<topic>"
      And agent cung cấp solution tương ứng cho từng cause
      And mỗi solution nêu rõ "ai thực hiện"

      Examples:
        | topic                          |
        | traffic congestion             |
        | work-related stress            |
        | rural-urban migration          |
        | obesity                        |
        | social media addiction         |
        | environmental pollution        |

  # ---------------------------------------------------------------------------
  # INTRODUCTION
  # ---------------------------------------------------------------------------

  Rule: Introduction phải nêu rõ essay sẽ xét causes AND solutions

    Scenario: Viết introduction cho Problem-Solution essay (Variant B — cause + solution)
      Given học sinh viết Problem-Solution essay dạng Variant B
      When agent hướng dẫn introduction
      Then agent cung cấp template:
        """
        [Paraphrase đề].
        This essay will examine the main reasons why [problem] has developed
        and suggest practical measures that could be taken to address it.
        """

    Scenario: Viết introduction cho Problem-Solution essay (Variant A — problem + solution)
      Given học sinh viết Problem-Solution essay dạng Variant A
      When agent hướng dẫn introduction
      Then agent cung cấp template:
        """
        [Paraphrase đề].
        This essay will explore the key problems this creates
        and propose several solutions that could be implemented.
        """

  # ---------------------------------------------------------------------------
  # BODY PARAGRAPHS
  # ---------------------------------------------------------------------------

  Rule: Body 1 = causes/problems, Body 2 = solutions — và solutions phải cụ thể

    Scenario: Hướng dẫn Body 1 (Causes/Problems)
      Given học sinh sắp viết body 1
      When agent hướng dẫn
      Then agent cung cấp template:
        """
        There are several reasons why [problem] has become so widespread.
        One major factor is [cause 1]. This is because [explanation].
        Another significant reason is [cause 2], particularly [detail].
        For example, in [country/context], [specific evidence].
        """
      And agent cung cấp useful phrases cho body 1:
        | phrase                                             |
        | One of the main causes of [problem] is...          |
        | A key factor contributing to [problem] is...       |
        | This can be attributed to...                       |
        | The situation has been exacerbated by...           |

    Scenario: Hướng dẫn Body 2 (Solutions)
      Given học sinh sắp viết body 2
      When agent hướng dẫn
      Then agent cung cấp template:
        """
        There are several effective measures that could be taken to tackle this problem.
        Firstly, [solution 1] could help address [cause 1]. [Explanation].
        In addition, [solution 2] would reduce [cause 2]. [Explanation].
        For instance, [city/country] has already implemented [solution] with positive results.
        """
      And agent cung cấp useful phrases cho body 2:
        | phrase                                             |
        | One effective solution would be to...              |
        | Governments could tackle this by...                |
        | A practical measure would be...                    |
        | This could be achieved through...                  |
        | If [action] were taken, [result] would follow.     |

    Scenario: Phát hiện solution quá chung chung
      Given học sinh viết solution "The government should do something about it"
      When agent review
      Then agent chỉ ra solution quá chung chung
      And agent hướng dẫn cụ thể hoá:
        """
        Thay vì: "The government should do something"
        Viết:    "The government could introduce a carbon tax on fossil fuels
                  to discourage excessive energy consumption."
        """
      And agent nhắc phải nêu rõ: ai làm, làm gì, tại sao hiệu quả

    Scenario: Kiểm tra solutions có match với causes
      Given học sinh đã viết xong cả body 1 và body 2
      When agent review cả 2 body
      Then agent kiểm tra từng solution có match với cause tương ứng không
      And nếu solution không liên quan đến cause đã nêu → agent yêu cầu điều chỉnh

  # ---------------------------------------------------------------------------
  # CONCLUSION
  # ---------------------------------------------------------------------------

  Rule: Conclusion phải tóm tắt causes VÀ solutions

    Scenario: Hướng dẫn viết Conclusion cho Problem-Solution essay
      Given học sinh đã viết xong body paragraphs
      When agent hướng dẫn conclusion
      Then agent cung cấp 2 template lựa chọn:
        | template | nội dung |
        | T1 | "In conclusion, [problem] is largely caused by [cause 1] and [cause 2]. However, if [solution 1] and [solution 2] were implemented, the situation could improve significantly." |
        | T2 | "To sum up, addressing [problem] requires action at multiple levels. Only through [solution 1] and [solution 2] can meaningful progress be achieved." |
      And agent nhắc "KHÔNG đưa nguyên nhân hoặc giải pháp mới vào conclusion"

  # ---------------------------------------------------------------------------
  # COMMON ERRORS
  # ---------------------------------------------------------------------------

  Scenario Outline: Phát hiện lỗi thường gặp trong Problem-Solution essay
    Given học sinh mắc lỗi "<loi>"
    When agent review bài
    Then agent chỉ ra lỗi và hướng dẫn sửa bằng tiếng Việt

    Examples:
      | loi                                                        |
      | Chỉ liệt kê problems, không có solutions                   |
      | Solutions không liên quan đến causes đã nêu                |
      | Solutions quá chung chung (không nêu ai làm và làm gì)     |
      | Nhầm Problem-Solution với Adv/Dis                          |
      | Body 2 (solutions) ngắn hơn body 1 đáng kể                 |
      | Conclusion đưa ra solution mới chưa đề cập trong body      |

  # ---------------------------------------------------------------------------
  # CHECKLIST
  # ---------------------------------------------------------------------------

  Scenario: Cung cấp checklist Problem-Solution trước khi nộp bài
    Given học sinh đã viết xong Problem-Solution essay
    When học sinh yêu cầu kiểm tra
    Then agent chạy checklist:
      | mục                                                             | pass/fail |
      | Xác định đúng variant (cause+sol / problem+sol)                 | ?         |
      | Introduction nêu rõ sẽ bàn causes AND solutions                 | ?         |
      | Body 1 chỉ có causes/problems                                   | ?         |
      | Body 2 chỉ có solutions                                         | ?         |
      | Mỗi solution match với cause tương ứng                          | ?         |
      | Solutions đủ cụ thể (nêu ai làm, làm gì)                       | ?         |
      | Conclusion tóm tắt causes + solutions, không có ý mới           | ?         |
      | Style formal, đủ 250 từ                                         | ?         |
