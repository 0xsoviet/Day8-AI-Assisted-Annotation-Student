# Lab #08 — mọi lệnh chỉ cần Python ≥ 3.8 (thư viện chuẩn). Gõ `make help` để xem.
PY ?= python3
LAB = $(PY) -m lab8

.PHONY: help init verify-data states lock install-reference profile rework frame-scores lock-ranking al-eval check-submission test check

help:
	@echo "Lab #08 — thứ tự dùng trong buổi:"
	@echo "  make init NAME=\"Họ Tên\" GITHUB_USER=tai-khoan   tự xác định lộ trình + chi phí, tạo submission/"
	@echo "  make verify-data                    kiểm data/ khớp SHA256SUMS"
	@echo "  make states                         4 trạng thái từ submission/assisted.xml"
	@echo "  make lock                           khóa phần (a)+(b), in mã gửi Lab Coach"
	@echo "  make install-reference ZIP=<file>   cài gói Lab Coach phát sau khi bạn khóa"
	@echo "  make profile                        error profile sau khi cài gói 1 (đọc cards/after-lock-card.md)"
	@echo "  make rework                         so bản khóa với submission/assisted_rework.xml"
	@echo "  make frame-scores                   điểm model + bản nháp ranking.csv (chỉ khi rank còn trống)"
	@echo "  make lock-ranking                   kiểm + khóa submission/ranking.csv"
	@echo "  make al-eval                        proxy của batch đã chọn (sau khi cài gói 2)"
	@echo "  make check-submission               kiểm gói nộp đủ và đúng dạng (không chấm điểm)"

init:
	@$(LAB) init --name "$(NAME)" --github-user "$(GITHUB_USER)"
verify-data:
	@$(LAB) verify-data
states:
	@$(LAB) states
lock:
	@$(LAB) lock
install-reference:
	@$(LAB) install-reference --zip "$(ZIP)"
profile:
	@$(LAB) profile
rework:
	@$(LAB) profile --rework
frame-scores:
	@$(LAB) frame-scores
lock-ranking:
	@$(LAB) lock-ranking
al-eval:
	@$(LAB) al-eval
check-submission:
	@$(LAB) check-submission

# Kiểm công cụ của repo (không đụng submission/ của bạn).
test:
	@$(PY) -m unittest discover -s tests -t . -q
check: verify-data test
