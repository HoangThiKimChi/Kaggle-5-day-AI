# language: vi
Feature: Hướng dẫn viết Opinion Essay (Agree/Disagree)
  Là một học sinh Việt Nam level A2-B1 đang ôn IELTS Writing Task 2
  Tôi muốn được hướng dẫn viết Opinion essay từng bước
  Để có thể viết bài hoàn chỉnh đạt band 5.0-6.0

  Background:
    Given học sinh có level "A2" hoặc "B1"
    And học sinh đang ôn IELTS Writing Task 2
    And agent đã load references từ "opinion_brainstorm.md" và "essay_templates.md"

  # ---------------------------------------------------------------------------
  # CLASSIFY
  # ---------------------------------------------------------------------------

  Rule: Agent phải nhận diện đúng Opinion essay

    Scenario Outline: Nhận diện Opinion essay qua keywords
      Given học sinh cung cấp đề bài "<prompt>"
      When agent gọi tool classify_essay_type
      Then kết quả phải là essay_type = "opinion"
      And agent phải trích xuất keyword "<keyword>" từ đề bài
      And agent giải thích bằng tiếng Việt tại sao đây là Opinion essay

      Examples:
        | prompt                                                                 | keyword                  |
        | Some people say music brings cultures together. To what extent do you agree or disagree? | to what extent           |
        | The working week should be shorter. Do you agree or disagree?          | do you agree or disagree |
        | Everyone should save money for the future. To what extent do you agree? | to what extent           |
        | In your opinion, should children learn money management at school?     | in your opinion          |
        | How far do you agree that technology has made life more complicated?   | how far do you agree     |

    Scenario: Không nhầm Opinion essay với Discussion essay
      Given đề bài chứa "discuss both views" VÀ "give your own opinion"
      When agent gọi classify_essay_type
      Then kết quả phải là essay_type = "discussion"
      And KHÔNG phải "opinion"

  # ---------------------------------------------------------------------------
  # BRAINSTORM
  # ---------------------------------------------------------------------------

  Rule: Agent phải hướng dẫn brainstorm đúng cách cho Opinion essay

    Scenario: Hướng dẫn phân tích đề trước khi brainstorm
      Given học sinh cung cấp đề bài Opinion essay bất kỳ
      When agent hướng dẫn bước phân tích đề
      Then agent phải yêu cầu học sinh xác định "topic words"
      And agent phải yêu cầu học sinh xác định "task words"
      And agent nhắc nhở "Answer the question, not just describe the topic"

    Scenario: Hướng dẫn chọn phía (agree/disagree) cho học sinh A2-B1
      Given học sinh là level "A2" hoặc "B1"
      And học sinh đang brainstorm Opinion essay
      When agent hướng dẫn chọn phía
      Then agent khuyên chọn "1 phía rõ ràng" (agree hoặc disagree hoàn toàn)
      And agent giải thích "Không nên viết partly agree ở level A2-B1 vì khó kiểm soát structure"
      And agent KHÔNG khuyên viết "balanced opinion" cho học sinh A2-B1

    Scenario Outline: Gợi ý ideas theo topic
      Given học sinh đã chọn phía "<stance>" cho đề về "<topic>"
      When agent gợi ý ideas cho body paragraphs
      Then agent phải cung cấp ít nhất 2 ideas cho phía "<stance>"
      And mỗi idea phải có ví dụ cụ thể liên quan đến "<context>"

      Examples:
        | topic       | stance   | context             |
        | technology  | agree    | cuộc sống hàng ngày |
        | technology  | disagree | tác hại xã hội      |
        | education   | agree    | trường học Việt Nam  |
        | environment | disagree | vai trò chính phủ   |
        | health      | agree    | người thu nhập thấp  |
        | society     | agree    | âm nhạc quốc tế     |

    Scenario: Hướng dẫn chọn 3 essay plans theo mức độ đồng ý
      Given học sinh đã chọn phía cho Opinion essay
      When agent gợi ý cách tổ chức bài
      Then agent phải trình bày 3 plans:
        | plan   | mô tả                                                    |
        | Plan 1 | Agree mạnh: 2 body paragraphs đều ủng hộ                 |
        | Plan 2 | Balanced: body1 ủng hộ, body2 phản đối, overall agree    |
        | Plan 3 | Disagree: acknowledge opposing view rồi phản bác 2 lần   |
      And agent khuyên học sinh A2-B1 dùng "Plan 1" vì đơn giản nhất

  # ---------------------------------------------------------------------------
  # INTRODUCTION
  # ---------------------------------------------------------------------------

  Rule: Agent phải hướng dẫn viết Introduction đúng chuẩn

    Scenario: Hướng dẫn viết Introduction cho Opinion essay
      Given học sinh đã classify đề là "opinion"
      And học sinh đã chọn phía (agree/disagree)
      When agent hướng dẫn viết introduction
      Then agent cung cấp template:
        """
        [Paraphrase đề]. I [strongly agree/disagree] with this view [for two main reasons /
        and in this essay I will explain why].
        """
      And agent cung cấp ví dụ hoàn chỉnh dựa trên đề bài của học sinh
      And agent liệt kê ít nhất 3 useful phrases để mở đầu introduction
      And agent nhắc "Introduction chỉ cần 2-3 câu, không viết quá dài"

    Scenario: Agent phát hiện học sinh copy nguyên văn đề bài
      Given học sinh nộp câu introduction chứa cụm từ nguyên văn từ đề bài
      When agent review introduction
      Then agent chỉ ra cụm từ bị copy
      And agent giải thích tại sao không được copy
      And agent gợi ý synonyms để paraphrase cụm từ đó
      And agent KHÔNG chấp nhận câu introduction đó

    Scenario: Kiểm tra thesis statement trong introduction
      Given học sinh đã viết introduction
      When agent kiểm tra introduction
      Then agent xác nhận có thesis statement rõ ràng (agree/disagree)
      And nếu thiếu thesis thì agent yêu cầu bổ sung
      And agent KHÔNG chấp nhận introduction mơ hồ không nêu rõ phía

  # ---------------------------------------------------------------------------
  # BODY PARAGRAPHS
  # ---------------------------------------------------------------------------

  Rule: Agent phải hướng dẫn viết Body paragraphs đúng cấu trúc

    Scenario: Hướng dẫn cấu trúc Body paragraph (Mindset L3)
      Given học sinh sắp viết body paragraph cho Opinion essay
      When agent hướng dẫn cấu trúc paragraph
      Then agent cung cấp cấu trúc 4 bước:
        | bước | nội dung                              |
        | 1    | Topic sentence (main idea)            |
        | 2    | Supporting idea (explain/cause-effect)|
        | 3    | Additional point (Not only that, but) |
        | 4    | Specific example (từ thực tế/VN)      |
      And agent cung cấp ví dụ paragraph hoàn chỉnh

    Scenario: Kiểm tra body paragraphs có 2 ideas khác nhau
      Given học sinh đã viết 2 body paragraphs
      When agent review body paragraphs
      Then agent kiểm tra body1 và body2 có ideas KHÁC NHAU không
      And nếu cùng idea thì agent chỉ ra và yêu cầu đổi body2
      And agent gợi ý idea mới phù hợp với topic

    Scenario: Phát hiện idea quá chung chung
      Given học sinh viết idea kiểu "Technology is good for people"
      When agent review idea đó
      Then agent chỉ ra idea quá chung chung
      And agent hướng dẫn cách cụ thể hoá:
        """
        Thêm: Why is it good? → How does it help? → Example?
        Ví dụ tốt hơn: "Technology saves time because people can pay bills
        online instead of going to the bank."
        """

    Scenario: Kiểm tra ví dụ cụ thể trong body paragraph
      Given học sinh viết body paragraph không có ví dụ
      When agent review paragraph đó
      Then agent nhắc nhở cần thêm ví dụ cụ thể
      And agent gợi ý ví dụ liên quan đến Việt Nam hoặc cuộc sống thực tế
      And agent giải thích tại sao ví dụ cụ thể giúp tăng điểm

  # ---------------------------------------------------------------------------
  # CONCLUSION
  # ---------------------------------------------------------------------------

  Rule: Agent phải hướng dẫn viết Conclusion đúng chuẩn

    Scenario: Hướng dẫn viết Conclusion cho Opinion essay
      Given học sinh đã viết introduction và body paragraphs
      When agent hướng dẫn viết conclusion
      Then agent cung cấp template:
        """
        In conclusion, I firmly believe that [restate position]
        because [brief summary of 2 reasons].
        """
      And agent nhắc "KHÔNG đưa ý mới vào conclusion"
      And agent nhắc "Restate opinion — KHÔNG copy nguyên câu từ introduction"

  # ---------------------------------------------------------------------------
  # COMMON ERRORS
  # ---------------------------------------------------------------------------

  Rule: Agent phải phát hiện và sửa lỗi thường gặp

    Scenario Outline: Phát hiện lỗi thường gặp trong Opinion essay
      Given học sinh mắc lỗi "<loi>"
      When agent review bài viết
      Then agent chỉ ra lỗi cụ thể
      And agent giải thích bằng tiếng Việt tại sao đây là lỗi
      And agent cung cấp cách sửa

      Examples:
        | loi                                                     |
        | Đổi ý kiến giữa bài (intro agree, body2 disagree)       |
        | 2 body paragraphs nói về cùng 1 idea                    |
        | Dùng ngôn ngữ informal (it's, they're, gonna)           |
        | Không có ví dụ cụ thể trong body                        |
        | Introduction copy nguyên văn từ đề bài                  |
        | Conclusion đưa ra ý mới chưa đề cập trong body          |

  # ---------------------------------------------------------------------------
  # FULL FLOW CHECKLIST
  # ---------------------------------------------------------------------------

  Rule: Agent phải cung cấp checklist hoàn chỉnh trước khi nộp bài

    Scenario: Cung cấp checklist cuối bài cho Opinion essay
      Given học sinh đã viết xong bài Opinion essay
      When học sinh yêu cầu check bài
      Then agent chạy qua checklist:
        | mục                                                          | pass/fail |
        | Introduction có paraphrase thực sự (không copy nguyên văn)   | ?         |
        | Có thesis statement rõ ràng (agree/disagree)                  | ?         |
        | Body 1 và Body 2 có 2 ideas KHÁC NHAU                        | ?         |
        | Mỗi body có topic sentence + explain + example                | ?         |
        | Conclusion restate opinion (không copy từ intro)              | ?         |
        | Không có ý mới trong conclusion                               | ?         |
        | Style formal (không dùng it's, gonna, BTW...)                 | ?         |
        | Đủ 250 từ trở lên                                             | ?         |
      And agent báo cáo từng mục pass hay fail
      And agent gợi ý cải thiện cho từng mục fail
