# language: vi
Feature: Hướng dẫn viết Discussion Essay (Discuss Both Views)
  Là một học sinh Việt Nam level A2-B1 đang ôn IELTS Writing Task 2
  Tôi muốn được hướng dẫn viết Discussion essay đúng cấu trúc
  Để không bỏ sót view nào và có ý kiến cá nhân rõ ràng

  Background:
    Given học sinh có level "A2" hoặc "B1"
    And agent đã load references từ "discussion_brainstorm.md" và "essay_templates.md"

  # ---------------------------------------------------------------------------
  # CLASSIFY
  # ---------------------------------------------------------------------------

  Rule: Agent phải nhận diện đúng Discussion essay

    Scenario Outline: Nhận diện Discussion essay qua keywords
      Given học sinh cung cấp đề bài "<prompt>"
      When agent gọi tool classify_essay_type
      Then kết quả phải là essay_type = "discussion"
      And agent phải trích xuất keyword "<keyword>"
      And agent giải thích bằng tiếng Việt: đây là Discussion essay, phải trình bày CẢ 2 phía

      Examples:
        | prompt                                                                                                       | keyword                        |
        | Some accept bad situations. Others try to improve. Discuss both views and give your own opinion.             | discuss both views             |
        | Some say species loss is the main env problem. Others disagree. Discuss both these views and give opinion.   | discuss both these views       |
        | Some think competition is good. Others prefer cooperation. Discuss both views and give your own opinion.     | discuss both views             |
        | Some believe cities are better. Others prefer countryside. Discuss both views.                               | discuss both views             |

    Scenario: Phân biệt Discussion với Opinion essay
      Given đề bài chỉ có "to what extent do you agree or disagree" và KHÔNG có "discuss both views"
      When agent gọi classify_essay_type
      Then kết quả phải là "opinion"
      And KHÔNG phải "discussion"

  # ---------------------------------------------------------------------------
  # BRAINSTORM
  # ---------------------------------------------------------------------------

  Rule: Agent phải hướng dẫn brainstorm đủ cả 2 phía

    Scenario: Hướng dẫn xác định 2 quan điểm đối lập trong đề
      Given học sinh cung cấp đề Discussion essay
      When agent hướng dẫn phân tích đề
      Then agent phải xác định rõ "View A là gì?" và "View B là gì?"
      And agent trình bày 2 views dưới dạng bảng đối lập
      And agent KHÔNG chỉ giải thích 1 phía

    Scenario Outline: Gợi ý ideas cân bằng cho cả 2 phía
      Given topic của Discussion essay là "<topic>"
      When agent gợi ý ideas
      Then agent phải cung cấp ít nhất 2 ideas cho View A "<view_a>"
      And agent phải cung cấp ít nhất 2 ideas cho View B "<view_b>"
      And 2 phía phải có độ dài ideas tương đương (cân bằng)

      Examples:
        | topic                  | view_a                     | view_b                        |
        | competition vs coop    | competition tốt cho xã hội | cooperation hiệu quả hơn      |
        | accept vs improve      | chấp nhận giúp tâm lý ổn   | cố gắng tạo thay đổi tích cực |
        | species vs climate     | mất loài là vấn đề chính   | biến đổi khí hậu quan trọng hơn |
        | city vs countryside    | thành phố có nhiều cơ hội  | nông thôn chất lượng sống tốt |

    Scenario: Hướng dẫn học sinh chọn personal opinion sau khi brainstorm
      Given học sinh đã brainstorm xong cả 2 phía
      When agent hỏi về personal opinion
      Then agent yêu cầu học sinh chọn phía mình nghiêng về hơn
      And agent giải thích: personal opinion xuất hiện ở introduction VÀ conclusion
      And agent giải thích: KHÔNG đưa "I believe" vào giữa body paragraphs

  # ---------------------------------------------------------------------------
  # INTRODUCTION
  # ---------------------------------------------------------------------------

  Rule: Agent hướng dẫn Introduction nêu đủ 3 thành phần

    Scenario: Introduction Discussion essay phải có 3 thành phần
      Given học sinh sắp viết introduction cho Discussion essay
      When agent hướng dẫn viết introduction
      Then agent cung cấp template với 3 thành phần rõ ràng:
        | thành phần | nội dung                                               |
        | 1          | Paraphrase đề bài                                      |
        | 2          | Acknowledge 2 phía tồn tại ("While some argue... others believe...") |
        | 3          | Thesis: mình nghiêng về phía nào ("This essay will argue that...") |
      And agent cung cấp ví dụ hoàn chỉnh dựa trên đề bài của học sinh

    Scenario: Kiểm tra introduction có đủ 3 thành phần
      Given học sinh đã viết introduction cho Discussion essay
      When agent review introduction
      Then agent kiểm tra từng thành phần:
        | thành phần    | có/không |
        | paraphrase    | ?        |
        | acknowledge   | ?        |
        | thesis        | ?        |
      And nếu thiếu thành phần nào thì agent yêu cầu bổ sung

  # ---------------------------------------------------------------------------
  # BODY PARAGRAPHS
  # ---------------------------------------------------------------------------

  Rule: Body 1 = View A, Body 2 = View B — tuyệt đối không trộn

    Scenario: Hướng dẫn cấu trúc Body 1 (View A)
      Given học sinh sắp viết body 1 của Discussion essay
      When agent hướng dẫn
      Then agent cung cấp template Body 1:
        """
        Those who support [View A] argue that [main reason].
        They point out that [explanation/evidence].
        For example, [specific example].
        """
      And agent nhắc: Body 1 chỉ trình bày View A, KHÔNG đề cập View B

    Scenario: Hướng dẫn cấu trúc Body 2 (View B)
      Given học sinh sắp viết body 2 của Discussion essay
      When agent hướng dẫn
      Then agent cung cấp template Body 2 với transition phrase:
        """
        On the other hand, those who favour [View B] believe that [main reason].
        They point to [evidence] to support their argument.
        For instance, [specific example].
        """
      And agent cung cấp danh sách transition phrases:
        | phrase                                                    |
        | On the other hand,                                        |
        | However, another school of thought suggests that...       |
        | In contrast, others believe that...                       |
        | Turning to the other side of the argument,                |

    Scenario: Phát hiện lỗi trộn 2 phía vào 1 body paragraph
      Given học sinh viết body 1 có cả View A lẫn View B
      When agent review body 1
      Then agent phát hiện lỗi trộn phía
      And agent giải thích: "Body 1 chỉ được trình bày 1 phía"
      And agent hướng dẫn tách phần View B sang body 2

    Scenario: Kiểm tra body paragraphs cân bằng về độ dài
      Given học sinh đã viết cả 2 body paragraphs
      When agent review
      Then agent kiểm tra độ dài 2 paragraphs
      And nếu 1 paragraph ngắn hơn đáng kể thì agent yêu cầu mở rộng
      And agent gợi ý thêm explanation hoặc example cho paragraph ngắn hơn

    Scenario: Phát hiện lỗi dùng "I" trong body paragraph Discussion
      Given học sinh viết "I think competition is good because..." trong body paragraph
      When agent review
      Then agent chỉ ra lỗi dùng "I" trong body
      And agent hướng dẫn thay bằng:
        """
        "Those who support competition argue that..."
        "Proponents of this view believe that..."
        """

  # ---------------------------------------------------------------------------
  # CONCLUSION
  # ---------------------------------------------------------------------------

  Rule: Conclusion phải tóm tắt cả 2 phía VÀ restate personal opinion

    Scenario: Hướng dẫn viết Conclusion cho Discussion essay
      Given học sinh đã viết xong body paragraphs
      When agent hướng dẫn viết conclusion
      Then agent cung cấp template:
        """
        In conclusion, although both perspectives have merit,
        I believe that [your position] is more convincing because [brief reason].
        """
      And agent cung cấp 3 mẫu conclusion theo mức độ đồng ý:
        | mức độ    | mẫu                                                                         |
        | agree A   | "While View B has some merit, View A is ultimately more persuasive because..." |
        | balanced  | "Both sides raise valid points; however, I lean towards View A overall."       |
        | agree B   | "Despite the appeal of View A, I am more convinced by View B since..."         |

  # ---------------------------------------------------------------------------
  # COMMON ERRORS
  # ---------------------------------------------------------------------------

  Rule: Agent phải phát hiện lỗi đặc trưng của Discussion essay

    Scenario Outline: Phát hiện lỗi thường gặp trong Discussion essay
      Given học sinh mắc lỗi "<loi>"
      When agent review bài
      Then agent chỉ ra lỗi và giải thích bằng tiếng Việt
      And agent cung cấp cách sửa cụ thể

      Examples:
        | loi                                                              |
        | Chỉ viết 1 phía, bỏ qua phía còn lại                            |
        | Không có personal opinion trong introduction và conclusion        |
        | Dùng "I believe" ở giữa body paragraph                          |
        | Body 1 ngắn hơn body 2 đáng kể (mất cân bằng)                  |
        | Trộn View A và View B vào cùng 1 body paragraph                 |
        | Conclusion không restate personal opinion                        |

  # ---------------------------------------------------------------------------
  # CHECKLIST
  # ---------------------------------------------------------------------------

  Scenario: Cung cấp checklist Discussion essay trước khi nộp bài
    Given học sinh đã viết xong Discussion essay
    When học sinh yêu cầu agent kiểm tra
    Then agent chạy checklist:
      | mục                                                                | pass/fail |
      | Introduction có acknowledge cả 2 phía                             | ?         |
      | Introduction có personal opinion/thesis rõ ràng                   | ?         |
      | Body 1 CHỈ trình bày View A                                       | ?         |
      | Body 2 CHỈ trình bày View B                                       | ?         |
      | Mỗi view có lý do + ví dụ                                         | ?         |
      | 2 body paragraphs cân bằng về độ dài (~100-120 từ mỗi paragraph) | ?         |
      | Conclusion tóm tắt 2 phía + restate position                      | ?         |
      | KHÔNG có "I believe/think" trong body paragraphs                  | ?         |
    And agent báo cáo pass/fail từng mục
    And agent gợi ý cải thiện cho mục fail
