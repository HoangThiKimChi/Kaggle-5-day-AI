# language: vi
Feature: Test Cases — Đề thật IELTS Writing Task 2
  Là developer đang build Essay Writing Coach agent
  Tôi muốn có bộ test cases từ đề thật Cambridge IELTS
  Để verify agent hoạt động đúng với cả 5 dạng đề

  Background:
    Given agent đã được khởi tạo với đầy đủ 5 tools
    And agent đã load tất cả references từ thư mục "references/"
    And học sinh có level "B1"

  # ===========================================================================
  # CAMBRIDGE IELTS 14
  # ===========================================================================

  Rule: Cambridge IELTS 14 — Test 1 (Discussion)

    Scenario: [Cam14-T1] Classify đúng Discussion essay
      Given học sinh cung cấp đề bài:
        """
        Some people believe that it is best to accept a bad situation, such as an
        unsatisfactory job or shortage of money. Others argue that it is better to
        try and improve such situations.
        Discuss both these views and give your own opinion.
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "discussion"
      And agent trích xuất keyword "discuss both these views"
      And agent giải thích: cần trình bày View A (accept) VÀ View B (improve) + personal opinion

    Scenario: [Cam14-T1] Gợi ý ideas cân bằng cho cả 2 phía
      Given đề bài Cam14-T1 đã được classify là "discussion"
      When agent gợi ý ideas cho brainstorm
      Then agent cung cấp ít nhất 2 ideas cho View A "chấp nhận hoàn cảnh xấu"
      And agent cung cấp ít nhất 2 ideas cho View B "cố gắng cải thiện hoàn cảnh"
      And ideas phải cụ thể, không chỉ là từ khoá

    Scenario: [Cam14-T1] Paraphrase đề bài
      Given đề bài Cam14-T1
      When agent gọi paraphrase_prompt với level "B1"
      Then agent trả về ít nhất 3 cách paraphrase
      And KHÔNG cách nào chứa cụm "accept a bad situation" nguyên văn
      And KHÔNG cách nào chứa cụm "try and improve" nguyên văn

  # ---------------------------------------------------------------------------

  Rule: Cambridge IELTS 14 — Test 2 (Discussion)

    Scenario: [Cam14-T2] Classify đúng Discussion essay — topic môi trường
      Given học sinh cung cấp đề bài:
        """
        Some people say that the main environmental problem of our time is the loss
        of particular species of plants and animals. Others say that there are more
        important environmental problems.
        Discuss both these views and give your own opinion.
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "discussion"
      And agent xác định View A = "mất loài là vấn đề môi trường chính"
      And agent xác định View B = "có vấn đề môi trường quan trọng hơn"

    Scenario: [Cam14-T2] Gợi ý vocabulary phù hợp topic Environment
      Given đề bài Cam14-T2 về môi trường
      When agent gọi enrich_vocabulary với topic "environment"
      Then agent gợi ý ít nhất 5 từ học thuật liên quan đến môi trường
      And danh sách phải bao gồm: "biodiversity", "extinction", "ecosystem"
      And mỗi từ có nghĩa tiếng Việt và ví dụ câu

  # ---------------------------------------------------------------------------

  Rule: Cambridge IELTS 14 — Test 3 (Opinion)

    Scenario: [Cam14-T3] Classify đúng Opinion essay — DEMO CASE CHÍNH
      Given học sinh cung cấp đề bài:
        """
        Some people say that music is a good way of bringing people of different
        cultures and ages together.
        To what extent do you agree or disagree with this opinion?
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "opinion"
      And agent trích xuất keyword "to what extent do you agree or disagree"
      And confidence phải là "high"

    Scenario: [Cam14-T3] Full flow — Introduction hoàn chỉnh
      Given đề bài Cam14-T3 đã classify là "opinion"
      And học sinh chọn phía "agree"
      And học sinh đã chọn paraphrase: "It has been suggested that music serves as a universal language..."
      When agent gọi guide_essay_section với section="introduction"
      Then agent trả về template introduction với thesis "I strongly agree"
      And agent cung cấp ví dụ introduction hoàn chỉnh (ít nhất 2 câu)
      And example KHÔNG chứa cụm nguyên văn từ đề bài

    Scenario: [Cam14-T3] Full flow — Body 1 với cấu trúc đúng
      Given đề bài Cam14-T3, section="body1", idea="music creates shared emotional experiences"
      When agent gọi guide_essay_section
      Then agent cung cấp template body 1 với 4 bước: topic sentence → explain → develop → example
      And agent gợi ý ví dụ cụ thể liên quan đến âm nhạc toàn cầu (K-pop, nhạc Latin...)

    Scenario: [Cam14-T3] Full flow — Enrich vocabulary từ đơn điệu
      Given học sinh viết: "Music is good. Music helps people. Music is important for culture."
      And topic = "society"
      When agent gọi enrich_vocabulary
      Then agent phát hiện "music" bị lặp 3 lần
      And agent gợi ý synonyms: "it", "such art form", "this medium"
      And agent phát hiện "good", "important" là từ đơn điệu
      And agent gợi ý: "beneficial", "significant", "crucial", "vital"

    Scenario: [Cam14-T3] Full flow — Suggest sentence structures
      Given học sinh viết: "Music is good. It helps people from different countries. They become friends."
      When agent gọi suggest_sentence_structures với level "B1"
      Then agent trả về ít nhất 3 variations
      And ít nhất 1 variation dùng pattern "Not only...but also"
      And ít nhất 1 variation dùng "which" relative clause

  # ---------------------------------------------------------------------------

  Rule: Cambridge IELTS 14 — Test 4 (Two-Part Question)

    Scenario: [Cam14-T4] Classify đúng Two-Part Question essay
      Given học sinh cung cấp đề bài:
        """
        Nowadays many people choose to be self-employed, rather than to work for
        a company or organisation.
        Why might this be the case?
        What could be the disadvantages of being self-employed?
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "two_part_question"
      And agent xác định Q1 = "Tại sao ngày càng nhiều người chọn tự kinh doanh?"
      And agent xác định Q2 = "Những bất lợi của việc tự kinh doanh là gì?"
      And agent cảnh báo: "Phải trả lời ĐỦ CẢ HAI câu hỏi"

    Scenario: [Cam14-T4] Gợi ý ideas riêng cho từng câu hỏi
      Given đề bài Cam14-T4 đã classify là "two_part_question"
      When agent gợi ý ideas
      Then agent gợi ý ít nhất 2 reasons cho Q1 (why self-employed)
      And agent gợi ý ít nhất 2 disadvantages cho Q2
      And ideas cho Q1 và Q2 phải được trình bày riêng biệt, rõ ràng

  # ===========================================================================
  # CAMBRIDGE IELTS 19
  # ===========================================================================

  Rule: Cambridge IELTS 19 — Test 1 (Discussion)

    Scenario: [Cam19-T1] Classify đúng Discussion essay — topic competition vs cooperation
      Given học sinh cung cấp đề bài:
        """
        Some people think that competition at work, at school and in daily life is a
        good thing. Others believe that we should try to cooperate more, rather than
        competing against each other.
        Discuss both these views and give your own opinion.
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "discussion"
      And agent xác định View A = "competition tốt"
      And agent xác định View B = "cooperation tốt hơn"

  # ---------------------------------------------------------------------------

  Rule: Cambridge IELTS 19 — Test 2 (Opinion)

    Scenario: [Cam19-T2] Classify đúng Opinion essay — topic working week
      Given học sinh cung cấp đề bài:
        """
        The working week should be shorter and workers should have a longer weekend.
        Do you agree or disagree?
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "opinion"
      And agent trích xuất keyword "do you agree or disagree"

    Scenario: [Cam19-T2] Paraphrase từ đề bài working week
      Given đề bài Cam19-T2
      When agent gọi paraphrase_prompt với level "B1"
      Then agent gợi ý synonyms:
        | từ gốc  | synonyms gợi ý                            |
        | workers | employees, the workforce, staff           |
        | shorter | reduced, condensed, fewer                 |
        | longer  | extended, additional                      |
      And 3 paraphrases phải dùng cấu trúc khác nhau (passive, noun phrase, verb phrase)

  # ---------------------------------------------------------------------------

  Rule: Cambridge IELTS 19 — Test 3 (Opinion)

    Scenario: [Cam19-T3] Classify đúng Opinion essay — topic saving money
      Given học sinh cung cấp đề bài:
        """
        It is important for everyone, including young people, to save money for
        their future.
        To what extent do you agree or disagree with this statement?
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "opinion"
      And agent gợi ý 2 hướng brainstorm: "agree fully" hoặc "partially agree"

  # ---------------------------------------------------------------------------

  Rule: Cambridge IELTS 19 — Test 4 (Adv/Dis — Outweigh)

    Scenario: [Cam19-T4] Classify đúng Adv/Dis essay — dạng outweigh
      Given học sinh cung cấp đề bài:
        """
        In many countries nowadays, consumers can go to a supermarket and buy food
        produced all over the world.
        Do you think this is a positive or negative development?
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "adv_dis"
      And agent xác định variant = "outweigh" (vì hỏi "positive or negative")
      And agent cảnh báo: "Conclusion phải kết luận rõ phía nào lớn hơn"

    Scenario: [Cam19-T4] Gợi ý vocabulary topic Globalisation và Food
      Given đề bài Cam19-T4 về globalisation và food
      When agent gọi enrich_vocabulary với topic "food"
      Then agent gợi ý ít nhất 5 từ liên quan
      And danh sách bao gồm các từ: "food security", "supply chain", "carbon footprint"

  # ===========================================================================
  # ĐỀ MẪU BỔ SUNG — PROBLEM-SOLUTION
  # ===========================================================================

  Rule: Problem-Solution — Traffic Congestion

    Scenario: [PS-1] Classify đúng Problem-Solution essay — traffic
      Given học sinh cung cấp đề bài:
        """
        Traffic congestion is a major problem in many cities around the world.
        What are the causes of this problem, and what measures could be taken to reduce it?
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "problem_solution"
      And agent xác định variant = "cause + solution"
      And agent gợi ý Variant B: Body 1 = Causes, Body 2 = Solutions

    Scenario: [PS-1] Kiểm tra solutions match với causes — traffic
      Given học sinh brainstorm:
        | causes                          | solutions                           |
        | Thiếu giao thông công cộng      | Phát triển metro/bus nhanh          |
        | Tăng sở hữu xe cá nhân          | Đánh thuế cao hơn vào xe cá nhân  |
      When agent review brainstorm
      Then agent xác nhận mỗi solution match đúng với cause
      And agent đánh giá solutions đủ cụ thể

  # ---------------------------------------------------------------------------

  Rule: Problem-Solution — Work Stress

    Scenario: [PS-3] Classify đúng Problem-Solution essay — work stress
      Given học sinh cung cấp đề bài:
        """
        Stress caused by work is becoming a major problem worldwide.
        What are the reasons for this? How could this problem be tackled?
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "problem_solution"
      And agent xác định: Q1 = "reasons for work stress", Q2 = "how to tackle"

  # ===========================================================================
  # ĐỀ MẪU BỔ SUNG — TWO-PART QUESTION
  # ===========================================================================

  Rule: Two-Part Question — Living Alone

    Scenario: [TPQ-1] Classify đúng Two-Part Question — living alone
      Given học sinh cung cấp đề bài:
        """
        In many countries, the number of people choosing to live alone is increasing.
        What are the reasons for this? Is it a positive or negative development?
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "two_part_question"
      And agent xác định Q1 = "reasons for living alone trend"
      And agent xác định Q2 = "positive or negative development"
      And agent cảnh báo không trộn 2 câu hỏi vào 1 body paragraph

  # ---------------------------------------------------------------------------

  Rule: Two-Part Question — Mobile Phones

    Scenario: [TPQ-2] Classify và gợi ý ideas — mobile phones youth
      Given học sinh cung cấp đề bài:
        """
        Young people are spending more and more time using mobile phones.
        Why is this? What effect does it have on young people and society?
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "two_part_question"
      And agent xác định Q1 = "why young people use more phones"
      And agent xác định Q2 = "effects on young people and society"
      And agent gợi ý ít nhất 2 reasons cho Q1
      And agent gợi ý ít nhất 2 effects cho Q2 (cả positive lẫn negative)

  # ---------------------------------------------------------------------------

  Rule: Two-Part Question — Social Media

    Scenario: [TPQ-3] Classify Two-Part Question — social media negative impact
      Given học sinh cung cấp đề bài:
        """
        Many people believe social networking sites such as Facebook have a hugely
        negative impact on both individuals and society.
        To what extent do you agree? What can be done to minimise the negative effects?
        """
      When agent gọi classify_essay_type
      Then essay_type phải là "two_part_question"
      And agent xác định Q1 = "extent of agreement on negative impact"
      And agent xác định Q2 = "measures to minimise negative effects"

  # ===========================================================================
  # CROSS-CUTTING SCENARIOS — kiểm tra hành vi chung của agent
  # ===========================================================================

  Rule: Agent phải nhất quán về ngôn ngữ giải thích

    Scenario: Agent giải thích bằng tiếng Việt cho mọi guidance
      Given học sinh gửi bất kỳ đề bài nào
      When agent cung cấp hướng dẫn
      Then mọi explanation phải bằng tiếng Việt
      And template và examples có thể bằng tiếng Anh
      And agent KHÔNG giải thích thuật ngữ kỹ thuật bằng tiếng Anh thuần túy

  Rule: Agent phải từ chối nếu đề bài không phải IELTS Writing Task 2

    Scenario: Agent nhận đề bài không hợp lệ
      Given học sinh cung cấp văn bản không phải đề IELTS Task 2
      When agent gọi classify_essay_type
      Then agent KHÔNG classify vào bất kỳ essay_type nào
      And agent giải thích: đây không phải đề IELTS Writing Task 2
      And agent hướng dẫn cách nhận biết đề Task 2 hợp lệ

  Rule: Agent phải recommend đúng tools theo flow

    Scenario Outline: Đúng thứ tự tools trong essay writing flow
      Given học sinh muốn viết bài "<essay_type>" cho đề bài "<prompt_snippet>"
      When agent bắt đầu hướng dẫn
      Then agent phải gọi tools theo thứ tự:
        | bước | tool                        |
        | 1    | classify_essay_type         |
        | 2    | paraphrase_prompt           |
        | 3    | guide_essay_section (intro) |
        | 4    | guide_essay_section (body1) |
        | 5    | guide_essay_section (body2) |
        | 6    | guide_essay_section (conclusion) |
      And agent có thể gọi suggest_sentence_structures hoặc enrich_vocabulary ở bất kỳ bước nào nếu cần

      Examples:
        | essay_type        | prompt_snippet                                  |
        | opinion           | Music brings cultures together. To what extent? |
        | discussion        | Competition vs cooperation. Discuss both views. |
        | adv_dis           | Working from home. Advantages and disadvantages.|
        | problem_solution  | Traffic congestion. Causes and solutions?       |
        | two_part_question | Living alone increasing. Why? Positive/negative?|
