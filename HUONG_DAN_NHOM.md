# Project 04 – IT Troubleshooting Expert System · Hướng dẫn cho nhóm

Đề gốc: <https://github.com/vinhnt21/ain-projects> → thư mục `project-04-it-expert-system` (đọc `README.md` trong đó).

**Trạng thái:** phần lõi AI và thí nghiệm của **midterm** đã xong và đã kiểm thử. Còn thiếu `presentation.pdf` (midterm) và toàn bộ phần final (UI Streamlit, `report.pdf` IEEE, repo GitHub).

## 1. Cài đặt (Windows, Python 3.11)

Mở PowerShell tại thư mục chứa file này:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r project-04-it-expert-system\requirements.txt
```

(Gõ thẳng `.venv\Scripts\python.exe` để khỏi phải `Activate.ps1`, vì lệnh đó hay bị Windows chặn.)

## 2. Chạy

| Mục đích | Lệnh |
|---|---|
| Toàn bộ test (80 test, ~10 s) | `.venv\Scripts\python.exe -m pytest project-04-it-expert-system\tests -q` |
| **Demo live** (giảng viên đưa triệu chứng nào cũng chạy được) | `.venv\Scripts\python.exe project-04-it-expert-system\starter\demo_cli.py SYM03 SYM04` |
| Demo hỏi-đáp: hệ thống tự hỏi câu tiếp theo | `.venv\Scripts\python.exe project-04-it-expert-system\starter\demo_cli.py --scenario SC04 --ask` |
| Đổi chiến lược phân xử | thêm `--strategy rule_count` (hoặc `coverage`) |
| Danh sách triệu chứng | `... demo_cli.py --list` |
| Chạy lại thí nghiệm (~8 s) | `.venv\Scripts\python.exe project-04-it-expert-system\experiments\ablation.py` |
| Chạy lại câu hỏi vấn đáp | `.venv\Scripts\python.exe project-04-it-expert-system\experiments\reasoning_probes.py` |
| App khung của giảng viên (chưa làm UI) | `.venv\Scripts\python.exe -m streamlit run project-04-it-expert-system\starter\app.py` |

## 3. Đọc theo thứ tự này

1. `project-04-it-expert-system/README.md`: đề bài, thang điểm.
2. `starter/student_core.py`: **lõi AI**. Phần đầu file có đoạn "Design in one paragraph" tóm tắt toàn bộ ý tưởng.
3. `experiments/results/ablation_report.md`: toàn bộ kết quả thí nghiệm E0–E9, dùng làm slide.
4. `experiments/results/reasoning_probes.md`: bằng chứng để trả lời câu `reasoning_probe` của từng kịch bản (giảng viên sẽ hỏi lúc vấn đáp).
5. `experiments/data_issues.md`: các lỗi dữ liệu nhóm tìm được, **cần hỏi giảng viên**.

## 4. Bản đồ file (★ = nhóm viết hoặc sửa, còn lại là của kit gốc, không đụng)

```
project-04-it-expert-system/
├── data/
│   ├── symptoms.json, causes.json, rules.json, scenarios.json   (kit gốc)
│   ├── conflicts.json        ★ 5 cặp triệu chứng mâu thuẫn (máy in), có lý do từng cặp
│   └── README.md             ★ thêm mục mô tả conflicts.json
├── starter/
│   ├── student_core.py       ★ LÕI AI: infer, explain, rank_candidates, diagnose, suggest_followups
│   ├── conflicts.py          ★ đọc + kiểm tra conflicts.json
│   ├── demo_cli.py           ★ demo dòng lệnh cho midterm
│   ├── rule_loader.py, app.py                                    (kit gốc)
├── tests/
│   ├── test_project_04_core.py   ★ 71 test cho lõi + script
│   └── test_project_04_sanity.py ★ test gốc, bỏ đúng 1 test "chưa implement" (xem chú thích trong file)
├── experiments/              ★
│   ├── ablation.py, reasoning_probes.py, data_issues.md
│   └── results/              bảng CSV, 2 biểu đồ PNG, 2 báo cáo .md (sinh tự động)
└── requirements.txt          ★ thêm pyarrow==17.0.0 (thiếu thì Streamlit crash với numpy 1.26)
```

## 5. Ý tưởng chính (để cả nhóm nói giống nhau khi vấn đáp)

- **Forward chaining:** bộ nhớ làm việc = triệu chứng báo cáo. Quét luật, luật nào đủ điều kiện thì kích hoạt và thêm kết luận vào bộ nhớ, lặp đến khi không còn luật mới (fixpoint). Mỗi lần kích hoạt được ghi vết, nên `explain` lấy lại được chuỗi chứng minh.
- **Không loại sớm:** mọi nguyên nhân có luật khớp đều được trả về. Không có luật nào khớp thì trả `[]`, không đoán.
- **Phân xử xung đột** là một bước riêng (`rank_candidates`, mặc định *specificity*): chỉ **xếp hạng**, không xoá ứng viên nào. Hoà thì báo hoà.
- **6 trạng thái:** `single_cause`, `resolved` (có đối thủ nhưng một bên trội hơn), `ambiguous` (hoà), `multi_fault` (nhiều lỗi độc lập), `contradictory`, `insufficient_evidence`.
- **Mâu thuẫn:** luật chỉ có điều kiện dương nên hệ thống **đơn điệu** (thêm bằng chứng không bao giờ rút lại kết luận) và không tự phát hiện được mâu thuẫn. Phải có ràng buộc ngoài (`conflicts.json`).
- **Chuyện R007 (SC04):** bỏ R007 thì CAUSE03 **vẫn là ứng viên** (R008, R043 còn kích hoạt), nhưng khi phân xử theo specificity thì CAUSE02 thành nguyên nhân duy nhất được chọn. Báo cáo phải nêu cả hai góc nhìn (E1).

## 6. Nhờ mọi người check

- [ ] Chạy được test và demo trên máy mình chưa? (lỗi gì thì chụp màn hình gửi nhóm)
- [ ] Bảng `data/conflicts.json`: có đồng ý 5 cặp mâu thuẫn và lý do không? Có cặp nào nên thêm hoặc bớt?
- [ ] `experiments/data_issues.md`: thống nhất danh sách câu hỏi gửi giảng viên (quan trọng nhất là **mục 1: CAUSE13/CAUSE14 của máy in bị đảo nhãn**).
- [ ] Đọc `student_core.py` và tự giải thích được từng hàm, vì vấn đáp chiếm 15 điểm.

## 7. Việc còn lại · gợi ý chia cho 3 người

| Người | Midterm | Final |
|---|---|---|
| A, lõi | Nắm chắc `student_core.py`, trả lời vấn đáp phần thuật toán, chốt `conflicts.json` | Hàm hỗ trợ cho UI, tích hợp |
| B, thí nghiệm | **Làm `presentation.pdf`** từ `ablation_report.md` + 2 biểu đồ | Phần thí nghiệm trong `report.pdf` |
| C, demo/UI | Tập demo bằng `demo_cli.py` (SC01, SC04, SC06, SC07) | UI Streamlit: tab 5 miền, hỏi tiếp, đồ thị suy luận, hành động khắc phục |

## 8. Lưu ý

- `.gitignore` gốc **loại thư mục `docs/`**: đừng để slide hay báo cáo trong đó, nếu không sẽ không commit được.
- Đề cấm thư viện rule engine (CLIPS, PyKE…) và LLM cho phần lõi; lõi hiện không dùng thư viện nào ngoài Python chuẩn.
- Mỗi máy tự tạo `.venv`; file zip không kèm thư mục này.
