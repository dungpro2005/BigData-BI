# Phân khúc khách hàng theo hành vi mua sắm

Pipeline RFM so sánh phân nhóm theo quintile với K-Means trên dữ liệu Online Retail II. Dữ liệu là giao dịch bán lẻ Anh Quốc, không phải dữ liệu lớn theo nghĩa phân tán; quy mô hiện tại phù hợp xử lý trên một máy bằng pandas.

## Câu hỏi kinh doanh và người dùng

1. Các nhóm khách hàng khác nhau thế nào về độ gần đây, tần suất, giá trị mua và đóng góp doanh thu?
2. Tỷ lệ khách hàng có giao dịch trong giai đoạn trước 01/06/2011 quay lại trong giai đoạn từ ngày đó trở đi là bao nhiêu?

Người dùng dự kiến: quản lý CRM/marketing và nhà phân tích dữ liệu. Cần xác nhận lại với nhóm học tập/giảng viên trước khi chốt báo cáo.

## Dữ liệu, nguồn và giới hạn

- Tệp chạy mặc định: `Kaggle/online_retail_II.csv` (đã có trong thư mục dự án).
- Nguồn tham khảo: [Kaggle - Online Retail II](https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci) và [UCI Machine Learning Repository - Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii).
- Bộ dữ liệu UCI được phát hành theo CC BY 4.0; cần giữ attribution và kiểm tra điều kiện phân phối của bản Kaggle đang dùng khi nộp/công khai repo.
- Phạm vi thời gian, số bản ghi, số trường, kiểu dữ liệu và tỷ lệ thiếu được tạo thực tế vào `reports/data_dictionary.csv` và `reports/quality_before_after.csv`.
- Customer ID bị thiếu; dữ liệu cũ (2009–2011), có nhiều khách hàng doanh nghiệp, không có chi phí marketing/lợi nhuận, và transaction không chứng minh rằng một khách là cá nhân duy nhất. Canceled invoices lưu riêng, không dùng trong RFM. Ngoại lệ dương được giữ; đặc trưng dùng `log1p`, không winsorize.
- Tệp nguồn 91 MB; chưa có bằng chứng về khả năng mở rộng phân tán. Không đưa dữ liệu cá nhân hoặc dữ liệu nguồn có điều kiện cấp phép chưa rõ lên repo công khai.

## Cấu trúc

```text
data/raw/                 # vị trí dữ liệu tùy chọn
data/processed/           # CSV giao dịch sạch, hóa đơn hủy, khách hàng/phân khúc
src/                      # load, clean, RFM, baseline, clustering, KPI, pipeline
tests/                    # kiểm thử làm sạch, RFM và KPI
dashboard/app.py          # Streamlit + Plotly
reports/                  # quality, dictionary, comparison, diagnostics, KPI, logs
requirements.txt
Makefile
```

## Cài đặt và chạy

Python 3.10+:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pytest -q
python3 -m src.pipeline
streamlit run dashboard/app.py
```

Hoặc dùng `make test`, `make pipeline`, `make dashboard`. Có thể truyền đường dẫn khác:

```bash
python3 -m src.pipeline --input /path/to/online_retail_II.csv
```

## Quy ước và phương pháp

- Snapshot là ngày cuối dữ liệu sạch cộng một ngày; Recency tính theo ngày, Frequency là số Invoice khác nhau, Monetary là tổng Revenue bằng GBP.
- Loại thiếu Customer ID, trùng hoàn toàn, ngày không hợp lệ, hóa đơn hủy khỏi tập mua hàng, Quantity/Price không dương và stock code dịch vụ/phí được nhận diện rõ trong mã. Tệp hóa đơn hủy được lưu riêng.
- `Revenue = Quantity × Price`. Không loại khách hàng giá trị cao; `log1p` trên R/F/M rồi StandardScaler.
- K-Means khảo sát k=2..10, xuất inertia/Silhouette/Davies–Bouldin; chọn k có Silhouette tốt nhất (phá hòa bằng Davies–Bouldin). `random_state=42`, `n_init=10`. Độ ổn định K-Means là ARI trung bình giữa seed 0 và bốn seed còn lại. Baseline quintile là xác định, ARI tự-so-sánh = 1.
- So sánh dùng cùng khách hàng và không gian RFM chuẩn hóa. Thời gian là trung bình 5 lần chạy riêng phần tạo nhãn. Baseline và K-Means không có nhãn chuẩn, do đó Silhouette/DB là chỉ số cấu trúc, không phải độ chính xác dự đoán.
- KPI quay lại cơ bản: khách có ít nhất hai Invoice khác nhau / tổng khách. KPI theo thời gian: khách có mua trước 01/06/2011 và mua ít nhất một lần từ ngày đó trở đi / khách có mua trước ngày đó.
- Dashboard lọc quốc gia, ngày mua gần nhất, phân khúc và phương pháp. Silhouette trong thẻ KPI được tính lại trên tập đang lọc, nếu có đủ ít nhất hai cụm.

## Đầu ra, insight và quyết định

Chạy pipeline sẽ tạo quality/data dictionary, so sánh phương pháp, chẩn đoán k, KPI thực đo, thông tin cấu hình máy, insight thực tế, bảng độ nhạy chiến dịch theo giả định và log có số dòng bị tác động/thời gian. Bảng phân khúc khách hàng và giao dịch sạch nằm trong `data/processed/`.

Không ghi số insight trước khi chạy dữ liệu thực. Khi chạy xong, dùng số thực trong `reports/kpi_summary.json`, `reports/comparison.csv` và `data/processed/customer_segments.csv` để nêu ít nhất ba insight trong báo cáo: tỷ trọng khách/doanh thu theo nhóm, RFM trung bình, tỷ lệ quay lại tổng thể và theo thời gian. Dashboard không thay cho ảnh chụp màn hình minh chứng; nhóm cần tự chụp các trạng thái lọc khi demo.

Đề xuất chiến dịch cần được xem là giả định kiểm thử, không phải dự báo lợi nhuận: duy trì đặc quyền cho Champions, cross-sell cho Loyal/Developing, voucher cá nhân hóa cho At-risk, và chỉ thử kênh chi phí thấp với Lost. Ước tính bằng số khách × chi phí giả định/khách so với phản hồi giả định × giá trị đơn trung bình; chạy sensitivity và A/B test có nhóm đối chứng trước khi áp dụng. Dữ liệu hiện tại không có margin/chi phí thực nên ROI không đại diện ROI tài chính thực tế.

Khi dùng AI, nhóm cần công khai cách sử dụng, kiểm tra lại kết quả, bổ sung báo cáo/slide/phân công và bảo đảm không nộp nguyên sản phẩm do AI tạo theo quy định học thuật.
