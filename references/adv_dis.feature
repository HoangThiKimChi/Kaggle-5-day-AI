# language: vi
Feature: Hướng dẫn viết Advantages & Disadvantages Essay
  Là một học sinh Việt Nam level A2-B1 đang ôn IELTS Writing Task 2
  Tôi muốn được hướng dẫn phân biệt và viết đúng Adv/Dis essay
  Để không nhầm lẫn giữa dạng "list" và "outweigh"

  Background:
    Given học sinh có level "A2" hoặc "B1"
    And agent đã load references từ "adv_dis_brainstorm.md" và "essay_templates.md"

  # ---------------------------------------------------------------------------
  # CLASSIFY
  # ---------------------------------------------------------------------------

  Rule: Agent phải nhận diện đúng Adv/Dis essay và phân biệt 2 biến thể

    Scenario Outline: Nhận diện Adv/Dis essay qua keywords
      Given học sinh cung cấp đề bài "<prompt>"
      When agent gọi classify_essay_type
      Then kết quả phải là essay_type = "adv_dis"
      And agent xác định biến thể "<variant>" (list hoặc outweigh)
      And agent giải thích sự khác biệt giữa 2 biến thể bằng tiếng Việt

      Examples:
        | prompt                                                                                                 | variant  |
        | What are the advantages and disadvantages of working from home?                                        | list     |
        | Discuss the advantages and disadvantages of children using smartphones at school.                      | list     |
        | Do the advantages of international travel outweigh the disadvantages?                                  | outweigh |
        | In many countries consumers buy food from all over the world. Is this positive or negative development? | outweigh |
        | Nowadays many people choose to be self-employed. Why might this be? What are the disadvantages?        | list     |

    Scenario: Agent giải thích sự khác biệt list vs outweigh
      Given học sinh hỏi sự khác biệt giữa "list" và "outweigh"
      When agent giải thích
      Then agent trình bày rõ:
        | biến thể | yêu cầu                                                   |
        | list     | Liệt kê adv + dis. KHÔNG cần kết luận phía nào lớn hơn   |
        | outweigh | Liệt kê adv + dis + KẾT LUẬN rõ phía nào lớn hơn         |
      And agent cung cấp ví dụ keywords cho mỗi biến thể

  # ---------------------------------------------------------------------------
  # BRAINSTORM
  # ---------------------------------------------------------------------------

  Rule: Agent phải hướng dẫn brainstorm đủ cả advantages lẫn disadvantages

    Scenario: Hướng dẫn 7 câu hỏi brainstorm cho Adv/Dis essay
      Given học sinh cần brainstorm cho Adv/Dis essay
      When agent hướng dẫn brainstorm
      Then agent dẫn qua 7 câu hỏi:
        | # | câu hỏi                                              |
        | 1 | Topic words là gì? Task words là gì?                  |
        | 2 | Đây là dạng "list" hay "outweigh"?                    |
        | 3 | Lợi ích trực tiếp nhất là gì?                         |
        | 4 | Ai được hưởng lợi? Hưởng lợi như thế nào?            |
        | 5 | Bất lợi rõ ràng nhất là gì?                           |
        | 6 | Ai bị ảnh hưởng tiêu cực? Như thế nào?               |
        | 7 | (Nếu outweigh) Lợi ích hay bất lợi lớn hơn tổng thể? |

    Scenario Outline: Gợi ý ideas theo topic
      Given topic của Adv/Dis essay là "<topic>"
      When agent gợi ý ideas
      Then agent cung cấp ít nhất 2 advantages cho "<topic>"
      And agent cung cấp ít nhất 2 disadvantages cho "<topic>"
      And mỗi idea có giải thích cụ thể (không chỉ liệt kê từ khoá)

      Examples:
        | topic                          |
        | working from home              |
        | children using smartphones     |
        | international food trade       |
        | people moving to cities        |
        | students studying abroad       |
        | self-employed / freelance work |

  # ---------------------------------------------------------------------------
  # INTRODUCTION
  # ---------------------------------------------------------------------------

  Rule: Introduction phải phù hợp với biến thể (list hoặc outweigh)

    Scenario: Viết introduction cho biến thể "list"
      Given học sinh viết Adv/Dis essay dạng "list"
      When agent hướng dẫn introduction
      Then agent cung cấp template:
        """
        [Paraphrase đề].
        This essay will examine both the advantages and disadvantages of [topic].
        """
      And agent KHÔNG yêu cầu học sinh nêu personal opinion trong introduction dạng list

    Scenario: Viết introduction cho biến thể "outweigh"
      Given học sinh viết Adv/Dis essay dạng "outweigh"
      When agent hướng dẫn introduction
      Then agent cung cấp template:
        """
        [Paraphrase đề].
        This essay will argue that, on balance, the advantages/disadvantages
        of [topic] outweigh the disadvantages/advantages.
        """
      And agent yêu cầu học sinh quyết định ngay từ đầu: advantages > disadvantages hay ngược lại

  # ---------------------------------------------------------------------------
  # BODY PARAGRAPHS
  # ---------------------------------------------------------------------------

  Rule: Body 1 = ONLY advantages, Body 2 = ONLY disadvantages

    Scenario: Hướng dẫn cấu trúc Body 1 (Advantages)
      Given học sinh sắp viết body 1 của Adv/Dis essay
      When agent hướng dẫn
      Then agent cung cấp template:
        """
        There are several clear advantages to [topic].
        Firstly, [main advantage], which means that [effect/explanation].
        For example, [specific example].
        Furthermore/In addition, [second advantage], as [explanation].
        """
      And agent nhắc: Body 1 chỉ viết về advantages, KHÔNG đề cập disadvantages

    Scenario: Hướng dẫn cấu trúc Body 2 (Disadvantages)
      Given học sinh sắp viết body 2 của Adv/Dis essay
      When agent hướng dẫn
      Then agent cung cấp template:
        """
        However, there are also significant drawbacks to [topic].
        The most serious is [main disadvantage], as [explanation].
        Moreover, [second disadvantage], which [effect].
        """
      And agent cung cấp transition phrases để mở body 2:
        | phrase                                              |
        | However, there are also significant drawbacks...    |
        | Despite these benefits, there are some concerns...  |
        | On the negative side,...                            |
        | Turning to the disadvantages,...                    |

    Scenario: Phát hiện lỗi trộn adv/dis trong cùng body paragraph
      Given học sinh viết body 1 có cả advantages lẫn disadvantages
      When agent review
      Then agent phát hiện lỗi trộn
      And agent giải thích: "Body 1 = ONLY advantages, Body 2 = ONLY disadvantages"
      And agent hướng dẫn tách phần disadvantages sang body 2

    Scenario: Phát hiện lỗi liệt kê quá nhiều ý nhỏ không phát triển
      Given học sinh liệt kê 5+ advantages mà không phát triển ý nào
      When agent review body 1
      Then agent chỉ ra lỗi liệt kê quá nhiều
      And agent hướng dẫn: "Chọn 2 advantages, phát triển kỹ từng ý với explain + example"
      And agent minh hoạ cách phát triển 1 advantage thành 3-4 câu

  # ---------------------------------------------------------------------------
  # CONCLUSION
  # ---------------------------------------------------------------------------

  Rule: Conclusion phải phù hợp với biến thể

    Scenario: Viết conclusion cho biến thể "list"
      Given học sinh viết Adv/Dis dạng "list"
      When agent hướng dẫn conclusion
      Then agent cung cấp template:
        """
        In conclusion, [topic] has both clear advantages and disadvantages.
        While [main advantage], there are also significant concerns about
        [main disadvantage]. It is important to [balanced recommendation].
        """
      And agent KHÔNG yêu cầu kết luận phía nào lớn hơn

    Scenario: Viết conclusion cho biến thể "outweigh" — advantages thắng
      Given học sinh viết Adv/Dis dạng "outweigh" và chọn advantages > disadvantages
      When agent hướng dẫn conclusion
      Then agent cung cấp template:
        """
        In conclusion, although [topic] has some drawbacks, particularly
        [main disadvantage], I believe the advantages are greater.
        [Main advantage] makes [topic] a worthwhile development overall.
        """

    Scenario: Viết conclusion cho biến thể "outweigh" — disadvantages thắng
      Given học sinh viết Adv/Dis dạng "outweigh" và chọn disadvantages > advantages
      When agent hướng dẫn conclusion
      Then agent cung cấp template:
        """
        In conclusion, while [topic] offers [main advantage], the disadvantages
        — especially [main disadvantage] — are too significant to ignore.
        Overall, I believe [topic] has a negative impact on [society/environment].
        """

    Scenario: Phát hiện lỗi thiếu kết luận trong đề outweigh
      Given học sinh viết Adv/Dis essay "outweigh" nhưng conclusion không nêu phía nào thắng
      When agent review conclusion
      Then agent chỉ ra lỗi thiếu verdict
      And agent yêu cầu học sinh thêm câu kết luận rõ ràng
      And agent giải thích đây là yêu cầu bắt buộc của dạng "outweigh"

  # ---------------------------------------------------------------------------
  # COMMON ERRORS
  # ---------------------------------------------------------------------------

  Scenario Outline: Phát hiện lỗi thường gặp trong Adv/Dis essay
    Given học sinh mắc lỗi "<loi>"
    When agent review bài
    Then agent chỉ ra lỗi và hướng dẫn sửa bằng tiếng Việt

    Examples:
      | loi                                                          |
      | Liệt kê 5+ ý nhỏ không phát triển ý nào                     |
      | Trộn adv và dis vào cùng 1 body paragraph                    |
      | Đề outweigh nhưng conclusion không kết luận phía nào lớn hơn |
      | Không có ví dụ cụ thể trong body                             |
      | Introduction copy nguyên văn từ đề bài                       |
      | Body 1 và Body 2 quá lệch về độ dài                          |

  # ---------------------------------------------------------------------------
  # CHECKLIST
  # ---------------------------------------------------------------------------

  Scenario: Cung cấp checklist Adv/Dis essay trước khi nộp bài
    Given học sinh đã viết xong Adv/Dis essay
    When học sinh yêu cầu kiểm tra
    Then agent chạy checklist:
      | mục                                                       | pass/fail |
      | Xác định đúng biến thể: list hay outweigh?                | ?         |
      | Body 1 CHỈ có advantages                                  | ?         |
      | Body 2 CHỈ có disadvantages                               | ?         |
      | Mỗi adv/dis có explain + example                          | ?         |
      | Nếu outweigh: conclusion có verdict rõ ràng               | ?         |
      | 2 body paragraphs cân bằng về độ dài                      | ?         |
      | Style formal, đủ 250 từ                                   | ?         |
    And agent báo cáo từng mục và gợi ý cải thiện
