# BÁO CÁO BÀI TẬP LỚN

## PHÂN KHÚC KHÁCH HÀNG THEO HÀNH VI MUA SẮM

**Học phần:** CO4033 – Phân tích dữ liệu lớn và Trí tuệ kinh doanh  
**Lĩnh vực:** CRM  
**Nhóm thực hiện:** [Tên nhóm / mã nhóm]  
**Thành viên:** [Họ tên – MSSV của từng thành viên]  
**Giảng viên:** [Họ tên giảng viên]  
**Lớp / học kỳ:** [Thông tin lớp / học kỳ]  
**Ngày hoàn thiện:** [Ngày nộp]

> **Hướng dẫn hoàn thiện:** Báo cáo này được soạn theo kết quả pipeline chạy trên tệp Online Retail II có trong dự án. Trước khi nộp, nhóm cần điền thông tin bìa, xác nhận thành viên và phân công, chèn ảnh dashboard/log chạy thật, kiểm tra lại đường dẫn nguồn và chính sách giấy phép, cũng như diễn giải lại bằng lời của nhóm theo quy định liêm chính học thuật. Báo cáo PDF 10–15 trang có thể tạo từ Markdown sau khi áp dụng định dạng Word, thêm bìa, sơ đồ và hình minh chứng.

---

## TÓM TẮT

Đề tài xây dựng một quy trình phân tích hành vi mua hàng nhằm hỗ trợ quản lý quan hệ khách hàng (CRM) nhận diện các nhóm khách có giá trị và mức độ gắn kết khác nhau. Dữ liệu sử dụng là Online Retail II, gồm 1.067.371 dòng giao dịch và 8 trường, ghi nhận từ ngày 01/12/2009 đến 09/12/2011. Sau xử lý thiếu mã khách hàng, trùng lặp, hóa đơn hủy, số lượng/đơn giá không hợp lệ và mã hàng dịch vụ, tập giao dịch hoạt động còn 776.589 dòng, 36.604 hóa đơn và 5.852 khách hàng có thể tính RFM.

Pipeline tính Recency, Frequency và Monetary theo từng khách hàng; áp dụng log1p và StandardScaler; sau đó so sánh baseline chấm điểm theo quintile với K-Means. Chọn số cụm bằng cách khảo sát k từ 2 đến 10, sử dụng Silhouette, Davies–Bouldin và inertia. K-Means chọn k=2 theo tiêu chí Silhouette cao nhất: Silhouette = 0,4381, Davies–Bouldin = 0,8732, ARI trung bình giữa các seed = 0,9969. Baseline tạo 6 nhóm theo quy tắc RFM: Silhouette = 0,1568, Davies–Bouldin = 1,4312. Các chỉ số phân cụm đánh giá cấu trúc hình học, không phải độ chính xác dự đoán vì bộ dữ liệu không có nhãn phân khúc chuẩn.

Tỷ lệ khách hàng có từ hai hóa đơn khác nhau trở lên trong toàn kỳ là 72,35%. Tỷ lệ khách có giao dịch trước ngày 01/06/2011 và tiếp tục mua từ ngày đó trở đi là 52,91%. Kết quả phân cụm cho thấy nhóm mang nhãn Champions có 2.335 khách (39,90%) nhưng đóng góp 87,71% doanh thu; nhóm At-risk/Lost có 3.517 khách (60,10%) và đóng góp 12,29%. Đây là mô tả dữ liệu lịch sử, không chứng minh rằng một chiến dịch marketing cụ thể sẽ tạo ra doanh thu tương ứng.

Dashboard Streamlit cung cấp bộ lọc quốc gia, ngày mua gần nhất, phương pháp và phân khúc; hiển thị các thẻ KPI, biểu đồ và bảng RFM. Đề xuất kinh doanh được xây dựng như giả thuyết để thử nghiệm. Ước tính chi phí và doanh thu trong báo cáo dùng giả định minh họa, không phải chi phí, lợi nhuận hay ROI thực tế. Dữ liệu đã cũ, thiếu Customer ID ở 22,77% dòng ban đầu và không có thông tin lợi nhuận/chi phí marketing; vì vậy cần cập nhật dữ liệu, chạy A/B test có nhóm đối chứng và kiểm tra điều kiện triển khai trước khi áp dụng.

**Từ khóa:** CRM, phân khúc khách hàng, RFM, K-Means, baseline, Silhouette, Streamlit.

---

## 1. GIỚI THIỆU

### 1.1. Bối cảnh

Trong bán lẻ, một doanh nghiệp có thể phục vụ đồng thời khách hàng mới, khách thường xuyên, khách có chi tiêu cao và khách đã lâu không quay lại. Nếu chỉ dùng doanh thu tổng hợp, nhà quản lý khó xác định nên ưu tiên nguồn lực chăm sóc cho nhóm nào. Phân khúc dựa trên hành vi giao dịch giúp chuyển dữ liệu hóa đơn thành các nhóm có thể diễn giải, từ đó hỗ trợ thiết kế thông điệp và chương trình chăm sóc khác nhau.

Đề tài sử dụng RFM vì ba thành phần có thể tính trực tiếp từ lịch sử giao dịch: độ gần đây của lần mua, số lần mua và tổng giá trị mua. K-Means được dùng để tìm nhóm dựa trên khoảng cách trong không gian đặc trưng; baseline theo ngưỡng/quintile cung cấp cách phân khúc đơn giản, dễ giải thích để làm mốc so sánh.

### 1.2. Vấn đề cần giải quyết

Đầu vào gồm các dòng giao dịch bán lẻ, không có nhãn khách hàng như “VIP” hay “có nguy cơ rời bỏ”. Cần xử lý dữ liệu giao dịch không hợp lệ và hóa đơn hủy, xác định tập khách có đủ thông tin, xây dựng đặc trưng ở cấp khách hàng, so sánh hai cách phân khúc trên cùng tập dữ liệu và tạo đầu ra trực quan để người phụ trách CRM có thể xem xét.

Bài toán này là **phân tích mô tả và phân cụm không giám sát**, không phải mô hình dự báo churn, doanh thu tương lai hay phản hồi marketing. Nhãn “At-risk/Lost” là cách gọi gợi ý dựa trên Recency/Frequency quan sát được, không phải xác nhận khách đã rời bỏ.

### 1.3. Mục tiêu

1. Khảo sát nguồn, schema, phạm vi thời gian và chất lượng dữ liệu.
2. Xây dựng pipeline có thể chạy lại: nạp dữ liệu, làm sạch, tạo RFM, chuẩn hóa, phân nhóm, tính KPI và xuất kết quả.
3. So sánh baseline quintile RFM với K-Means theo Silhouette, Davies–Bouldin, độ ổn định ARI, số nhóm, thời gian và khả năng diễn giải.
4. Trình bày kết quả trên dashboard Streamlit với bộ lọc và biểu đồ phù hợp.
5. Đề xuất hành động CRM có nêu rõ giả định, chi phí, rủi ro và cách kiểm chứng.

### 1.4. Câu hỏi phân tích

**Q1.** Các nhóm khách hàng khác nhau như thế nào về Recency, Frequency, Monetary, quy mô khách và tỷ trọng doanh thu?

**Q2.** Trong số khách hàng có ít nhất một giao dịch trước ngày 01/06/2011, tỷ lệ nào tiếp tục có giao dịch từ ngày 01/06/2011 đến hết dữ liệu?

Q1 được trả lời bằng bảng RFM và tỷ trọng theo phân khúc. Q2 được trả lời bằng phép giao giữa tập khách có giao dịch ở giai đoạn trước và tập khách có giao dịch ở giai đoạn sau. Mốc thời gian là quy ước phân tích của đề tài, không phải bằng chứng về tác động của chiến dịch.

### 1.5. Người dùng dự kiến

- **Quản lý CRM/marketing:** xem quy mô và giá trị từng phân khúc, cân nhắc ưu tiên chăm sóc.
- **Chuyên viên marketing:** lựa chọn nhóm thử nghiệm chiến dịch và theo dõi phản hồi.
- **Nhà phân tích dữ liệu:** chạy lại pipeline, đối chiếu chất lượng dữ liệu và giải thích chỉ số.

Người dùng cuối chính cần được nhóm xác nhận với giảng viên hoặc đơn vị giả định trước khi chốt báo cáo.

### 1.6. Phạm vi

Phân tích tập trung vào giao dịch mua hợp lệ có Customer ID, với số lượng và giá dương. Hóa đơn hủy được lưu riêng, không dùng trong RFM. Doanh thu tính theo Quantity × Price và được xem là doanh thu dòng hàng quy đổi GBP, không phải lợi nhuận. Các giá trị dương lớn được giữ lại; log1p được áp dụng khi tạo đặc trưng, không winsorize và không loại khách có giá trị lớn.

---

## 2. DỮ LIỆU VÀ QUẢN LÝ DỮ LIỆU

### 2.1. Nguồn dữ liệu

Dữ liệu đầu vào trong workspace là `Kaggle/online_retail_II.csv`. Nguồn tham khảo:

1. Kaggle, *Online Retail II*: <https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci>
2. UCI Machine Learning Repository, *Online Retail II*: <https://archive.ics.uci.edu/dataset/502/online+retail+ii>

UCI ghi nhận bộ dữ liệu theo giấy phép CC BY 4.0; khi tái phân phối cần ghi attribution phù hợp. Nhóm cần kiểm tra chính sách của bản tải từ Kaggle trước khi đưa dữ liệu vào repo hoặc gửi kèm báo cáo. Tệp CSV nguồn không được đưa vào repo mã nguồn mặc định.

### 2.2. Quy mô và phạm vi

| Thuộc tính | Kết quả |
|---|---:|
| Số dòng ban đầu | 1.067.371 |
| Số cột | 8 |
| Thời điểm nhỏ nhất | 01/12/2009 07:45 |
| Thời điểm lớn nhất | 09/12/2011 12:50 |
| Dòng sau làm sạch để phân tích | 776.589 |
| Khách hàng sau làm sạch | 5.852 |
| Hóa đơn sau làm sạch | 36.604 |
| Hóa đơn hủy được tách riêng | 18.390 |

Mặc dù có hơn một triệu dòng, thử nghiệm được thực hiện trên một máy và chưa chứng minh khả năng mở rộng phân tán. Vì vậy, báo cáo không kết luận đây là Big Data theo nghĩa hệ thống phân tán; đây là bài toán phân tích dữ liệu bán lẻ có quy mô đủ lớn để minh họa pipeline và BI trên máy đơn.

### 2.3. Từ điển dữ liệu

Tỷ lệ thiếu được tính trên dữ liệu nguồn trước khi làm sạch.

| Trường | Kiểu dữ liệu khi nạp | Ý nghĩa | Thiếu (%) |
|---|---|---|---:|
| Invoice | string | Mã hóa đơn; mã bắt đầu bằng C biểu thị hóa đơn hủy | 0,00 |
| StockCode | string | Mã hàng hoặc mã dịch vụ | 0,00 |
| Description | object/string | Mô tả mặt hàng | 0,41 |
| Quantity | int64 | Số lượng trên dòng hóa đơn | 0,00 |
| InvoiceDate | object/string | Thời điểm giao dịch; chuyển sang datetime trong pipeline | 0,00 |
| Price | float64 | Đơn giá, GBP | 0,00 |
| Customer ID | float64 | Mã định danh khách hàng giả danh; thiếu được lưu dưới dạng NaN | 22,77 |
| Country | object/string | Quốc gia của khách hàng | 0,00 |

Customer ID là mã định danh giả danh chứ không phải dữ liệu nhận dạng trực tiếp. Tuy nhiên, thiếu mã khách hàng khiến các dòng này không thể gắn vào hồ sơ RFM nên bị loại khỏi phân tích khách hàng. Description thiếu không được dùng làm khóa phân cụm; dòng đó vẫn có thể được giữ nếu các trường điều kiện khác hợp lệ.

### 2.4. Chất lượng và làm sạch

Các quy tắc được áp dụng tuần tự. “Dòng bị ảnh hưởng” dưới đây là số dòng rời khỏi tập giao dịch đang dùng sau từng bước. Hóa đơn hủy được lưu riêng, không được xem là giao dịch mua hợp lệ.

| Giai đoạn | Dòng còn lại | Dòng bị loại khỏi tập hoạt động ở bước này | Thiếu (%) | Trùng hoàn toàn (%) |
|---|---:|---:|---:|---:|
| Ban đầu | 1.067.371 | 0 | 2,90 | 3,22 |
| Loại thiếu Customer ID | 824.364 | 243.007 | 0,00 | 3,21 |
| Loại trùng hoàn toàn | 797.885 | 26.479 | 0,00 | 0,00 |
| Chuyển ngày và loại ngày không hợp lệ | 797.885 | 0 | 0,00 | 0,00 |
| Tách hóa đơn hủy | 779.495 | 18.390 | 0,00 | 0,00 |
| Loại Quantity ≤ 0 hoặc Price ≤ 0 | 779.425 | 70 | 0,00 | 0,00 |
| Loại stock code dịch vụ/phí | 776.589 | 2.836 | 0,00 | 0,00 |

Tổng dòng rời tập hoạt động là 290.782, bằng chênh lệch giữa số dòng ban đầu và số dòng cuối. Tỷ lệ thiếu/trùng tính theo số ô thiếu hoặc số dòng trùng trên bảng ở mỗi thời điểm, không phải tỷ lệ khách hàng. “Trùng hoàn toàn” được xác định trên toàn bộ các cột.

Các quyết định làm sạch:

1. **Thiếu Customer ID:** loại khỏi RFM vì không thể gán giao dịch cho khách. Đây là bước ảnh hưởng nhiều nhất, 243.007 dòng (22,77% dữ liệu nguồn).
2. **Trùng hoàn toàn:** xóa bản ghi trùng nhằm tránh tính lặp doanh thu và tần suất.
3. **InvoiceDate:** chuyển sang datetime; dữ liệu mẫu thực tế không phát sinh ngày không hợp lệ sau chuyển đổi.
4. **Hóa đơn hủy:** nhận diện mã Invoice bắt đầu bằng C và tách 18.390 dòng vào `data/processed/cancellations.csv`.
5. **Số lượng/giá:** loại các dòng có Quantity hoặc Price không dương. Dữ liệu âm thường có thể là điều chỉnh/hoàn trả; không được diễn giải thành giao dịch mua trong chỉ số chính.
6. **StockCode phi sản phẩm:** loại nhóm mã được nhận diện trong mã nguồn như postage, bank charges, adjustment, test và các mã dịch vụ đã liệt kê. Bộ lọc dựa trên danh sách/mẫu mã, do đó có thể chưa bao phủ mọi mã phi sản phẩm.
7. **Ngoại lệ:** giữ khách hàng chi tiêu cao và giá trị dương lớn. Áp dụng log1p khi biến đổi RFM để giảm lệch phải; không winsorize.
8. **Doanh thu dòng hàng:** tạo `Revenue = Quantity × Price`; đơn vị tiền tệ là GBP theo mô tả dữ liệu.

Kết quả chất lượng được lưu ở `reports/quality_before_after.csv`; từ điển dữ liệu ở `reports/data_dictionary.csv`.

---

## 3. KIẾN TRÚC VÀ QUY TRÌNH THỰC HIỆN

### 3.1. Kiến trúc pipeline

```text
Online Retail II CSV
        |
        v
Nạp dữ liệu và kiểm tra schema
        |
        v
Làm sạch: thiếu ID / trùng / ngày / hóa đơn hủy /
Quantity-Price / mã dịch vụ
        |----------------------> Lưu hóa đơn hủy riêng
        v
Giao dịch hợp lệ + Revenue
        |
        v
RFM theo Customer ID
        |
        v
log1p(R, F, M) -> StandardScaler
        |
        +----------------------------+
        |                            |
        v                            v
Baseline quintile RFM           K-Means (k=2..10)
        |                            |
        +--------------+-------------+
                       v
KPI / so sánh / phân khúc / log / báo cáo
                       |
                       v
Dashboard Streamlit + Plotly
                       |
                       v
Insight và đề xuất CRM cần kiểm chứng
```

### 3.2. Công nghệ

- Python 3.10.12
- pandas 2.3.3
- scikit-learn 1.7.2
- Streamlit và Plotly cho dashboard
- pytest cho kiểm thử
- CSV/JSON cho các đầu ra có thể truy vết

### 3.3. Tái lập

Từ thư mục dự án, cài `requirements.txt`, chạy `python3 -m pytest -q`, sau đó `python3 -m src.pipeline` và `streamlit run dashboard/app.py`. Pipeline mặc định đọc tệp CSV hiện có trong `Kaggle/`; có thể truyền đường dẫn khác bằng tham số `--input`.

Pipeline xuất giao dịch sạch, hóa đơn hủy, bảng khách hàng/phân khúc, từ điển dữ liệu, chất lượng trước–sau, chẩn đoán k, bảng so sánh, KPI, cấu hình máy và log. CSV nguồn và CSV giao dịch xử lý được loại khỏi Git theo `.gitignore`; người nộp cần cung cấp đường dẫn nguồn hợp lệ thay vì đưa dữ liệu vào repo nếu điều kiện cấp phép chưa rõ.

### 3.4. Cấu hình môi trường chạy

| Thành phần | Thông tin ghi nhận |
|---|---|
| Hệ điều hành | Linux 6.8.0-149-generic, x86_64 |
| CPU | Không lấy được model CPU từ runtime; kiến trúc x86_64 |
| Số luồng logic | 16 |
| RAM nhận diện | 15,33 GiB |
| Python | 3.10.12 |
| pandas | 2.3.3 |
| scikit-learn | 1.7.2 |

Thông số là môi trường chạy pipeline tại thời điểm ghi log, không phải benchmark phần cứng độc lập. Nếu chạy trên máy khác, thời gian và kết quả có thể khác; cần lưu cấu hình thực tế tại máy demo/nộp.

---

## 4. PHƯƠNG PHÁP PHÂN TÍCH

### 4.1. Định nghĩa RFM

Mốc snapshot được đặt bằng ngày cuối cùng có giao dịch sạch cộng một ngày:

\[
\text{Snapshot} = \max(\text{InvoiceDate}) + 1\text{ ngày}
\]

Với dữ liệu hiện tại, snapshot là **10/12/2011**.

- **Recency (R):** số ngày lịch giữa snapshot và ngày mua gần nhất của khách.  
  \(R_i = \text{Snapshot} - \max(\text{InvoiceDate}_i)\)
- **Frequency (F):** số hóa đơn khác nhau của khách trong toàn kỳ.  
  \(F_i = |\{\text{Invoice}_i\}|\)
- **Monetary (M):** tổng doanh thu dòng hàng hợp lệ của khách, GBP.  
  \(M_i = \sum \text{Revenue}_i\)

R được tính theo ngày lịch, không theo phần lẻ của 24 giờ. Trong quá trình kiểm tra, phép tính cũ lấy chênh lệch timestamp rồi cắt phần thập phân có thể khiến một giao dịch trong ngày trước snapshot bị tính thấp hơn một ngày; phép tính đã được hiệu chỉnh và test RFM đã được chạy lại trước khi chốt số liệu báo cáo.

### 4.2. Biến đổi và chuẩn hóa

Phân phối Frequency và Monetary thường lệch phải, và Recency có thể lệch. Đề tài áp dụng log1p cho cả ba đặc trưng:

\[
x' = \log(1+x)
\]

Sau đó dùng StandardScaler để đưa R, F, M về cùng thang đo trung bình 0 và độ lệch chuẩn 1. K-Means và các phép so sánh Silhouette/Davies–Bouldin sử dụng cùng không gian đặc trưng đã chuẩn hóa.

### 4.3. Baseline quintile

Với mỗi đặc trưng, tính thứ hạng khách hàng và chia thành năm nhóm phân vị. Recency có hướng điểm ngược: khách mua càng gần đây được điểm R càng cao; Frequency và Monetary càng cao thì điểm tương ứng càng cao. Quy tắc gộp thành nhãn được xây dựng từ điểm R/F/M: Champions, Loyal, At-risk, Lost, New/Promising và Regular theo điều kiện trong mã nguồn. Trên dữ liệu hiện tại có **6 nhãn baseline thực tế**.

Baseline dễ giải thích và xác định lặp lại. Tuy nhiên, cách chia theo phân vị không nhất thiết phù hợp với cấu trúc tự nhiên của khách hàng; một khách có thể nằm gần ngưỡng nhưng bị chuyển nhóm bởi phân vị.

### 4.4. K-Means và lựa chọn k

K-Means tối thiểu hóa tổng bình phương khoảng cách từ điểm dữ liệu đến tâm cụm:

\[
J = \sum_{j=1}^{k} \sum_{x_i \in C_j} \lVert x_i - \mu_j \rVert^2
\]

Thử nghiệm k=2..10, dùng `random_state=42` và `n_init=10`. Với mỗi k ghi lại:

- **Inertia:** tổng bình phương khoảng cách trong cụm; thường giảm khi k tăng.
- **Silhouette:** mức độ một điểm gần cụm của nó so với cụm kế tiếp.
- **Davies–Bouldin:** mức độ tương tự trung bình giữa mỗi cụm và cụm gần nhất; thường thấp hơn là tốt hơn.

Chương trình lựa chọn k có Silhouette cao nhất, dùng Davies–Bouldin làm tiêu chí phụ. Kết quả chọn k=2. Đây là quyết định theo tiêu chí hình học đã định trước; số cụm thấp làm giảm độ chi tiết nghiệp vụ. Nhóm cần nêu rõ đánh đổi này, không ép mô hình tạo 4–5 nhóm chỉ vì đó là số thường thấy.

### 4.5. Định nghĩa KPI và đánh giá

**Silhouette** cho một khách:

\[
s(i) = \frac{b(i)-a(i)}{\max(a(i),b(i))}
\]

Trong đó \(a(i)\) là khoảng cách trung bình trong cùng cụm, \(b(i)\) là khoảng cách trung bình nhỏ nhất đến cụm khác. Điểm tổng thể là trung bình \(s(i)\) của mọi khách; không có đơn vị, nằm trong [-1, 1]. Điểm cao hơn gợi ý cụm tách biệt hơn theo không gian đặc trưng, không có nghĩa là phân khúc “đúng” theo nhãn kinh doanh.

**Tỷ lệ khách quay lại trong toàn kỳ:**

\[
\frac{\#\{\text{khách có ít nhất 2 Invoice khác nhau}\}}
{\#\{\text{khách có giao dịch hợp lệ}\}}\times 100\%
\]

**Tỷ lệ mua lại qua mốc thời gian:** mẫu số là khách có ít nhất một giao dịch trước 01/06/2011; tử số là khách thuộc mẫu số đồng thời có ít nhất một giao dịch từ 01/06/2011 trở đi.

**ARI (Adjusted Rand Index):** so sánh mức nhất quán giữa hai lần gán cụm, điều chỉnh theo mức trùng hợp ngẫu nhiên. K-Means được chạy qua 5 seed (0–4); ARI báo cáo là trung bình so với lần seed đầu. Baseline không ngẫu nhiên nên ARI tự-so-sánh được ghi là 1,0; con số này chỉ nói baseline tái lập xác định, không phải chất lượng phân khúc cao hơn.

Không có nhãn chuẩn để tính accuracy/precision/recall. Silhouette và Davies–Bouldin là các chỉ số nội tại, cần kết hợp hồ sơ RFM và đánh giá nghiệp vụ.

---

## 5. KIỂM THỬ VÀ KIỂM SOÁT ĐÚNG ĐẮN

Pipeline có bốn test, đã chạy thành công (**4 passed**):

| Test | Kiểm tra |
|---|---|
| Làm sạch mẫu | Dòng thiếu Customer ID bị loại; hóa đơn C được tách; Price=0 bị loại; chỉ còn giao dịch hợp lệ |
| RFM mẫu | Tạo dữ liệu 3 khách, tính tay Recency/Frequency/Monetary; xác nhận hai dòng cùng Invoice chỉ tính một hóa đơn |
| KPI mẫu | Tỷ lệ khách có ít nhất 2 Invoice và Silhouette trên dữ liệu nhỏ; đối chiếu trực tiếp `sklearn.metrics.silhouette_score` |
| Nhất quán đầu ra | Nếu có đầu ra pipeline, kiểm tra KPI của dashboard khớp khách, doanh thu, tỷ lệ quay lại và Silhouette toàn tập |

RFM test bao gồm timestamp ở các giờ khác nhau trong ngày để kiểm tra Recency theo ngày lịch. Các test mẫu giúp kiểm chứng logic cốt lõi, nhưng không thay cho kiểm tra dữ liệu nguồn, review code hoặc kiểm tra người dùng trên dashboard.

---

## 6. KẾT QUẢ THỰC NGHIỆM

### 6.1. Kết quả chọn k

| k | Inertia | Silhouette | Davies–Bouldin |
|---:|---:|---:|---:|
| 2 | 8.546,85 | **0,4381** | **0,8732** |
| 3 | 6.315,37 | 0,3482 | 1,0347 |
| 4 | 4.878,90 | 0,3664 | 0,9291 |
| 5 | 4.058,18 | 0,3441 | 0,9488 |
| 6 | 3.525,32 | 0,3367 | 0,9651 |
| 7 | 3.159,47 | 0,3056 | 0,9844 |
| 8 | 2.875,61 | 0,2957 | 1,0006 |
| 9 | 2.630,54 | 0,2875 | 1,0348 |
| 10 | 2.439,29 | 0,2890 | 1,0165 |

Inertia giảm khi số cụm tăng, như kỳ vọng. Silhouette cao nhất tại k=2. k=4 có Silhouette 0,3664, thấp hơn k=2 nhưng tạo thêm sắc thái; nếu mục tiêu nghiệp vụ cần phân biệt nhóm trung gian, nhóm có thể chạy thử k=4 và đánh giá thêm tính ổn định/khả năng hành động, song không nên thay số liệu k=2 trong kết quả chính khi quy tắc chọn k vẫn là Silhouette cao nhất.

### 6.2. Hồ sơ hai cụm K-Means

| Nhãn diễn giải | Số khách | Recency trung bình (ngày) | Frequency trung bình (hóa đơn) | Monetary trung bình (GBP) |
|---|---:|---:|---:|---:|
| At-risk/Lost (C0) | 3.517 | 299,67 | 2,08 | 596,60 |
| Champions (C1) | 2.335 | 51,72 | 12,54 | 6.411,38 |

Nhóm At-risk/Lost có lần mua gần nhất xa hơn, tần suất và chi tiêu thấp hơn nhóm Champions trong dữ liệu quan sát. “At-risk/Lost” là nhãn mô tả tương đối dựa trên RFM; không có dữ liệu nhãn rời bỏ và không thể kết luận từng khách sẽ không quay lại. Tương tự, “Champions” không phải nhãn do doanh nghiệp cung cấp mà là tên diễn giải cụm được tạo sau khi xem RFM trung bình.

### 6.3. So sánh baseline và K-Means

| Phương pháp | Số nhóm | Silhouette | Davies–Bouldin | ARI ổn định | Thời gian trung bình / lần (giây) | Diễn giải |
|---|---:|---:|---:|---:|---:|---|
| Baseline quintile RFM | 6 | 0,1568 | 1,4312 | 1,0000* | 0,00716 | Quy tắc rõ, dễ giải thích; chia theo phân vị |
| K-Means, k=2 | 2 | **0,4381** | **0,8732** | 0,9969 | 0,01985 | Phân nhóm theo cấu trúc khoảng cách, cần diễn giải tâm cụm |

`*` ARI baseline bằng 1 do baseline xác định, không ngẫu nhiên; không thể so sánh trực tiếp như một điểm “ổn định hơn” có ý nghĩa phân cụm.

Thời gian trong bảng là trung bình của 5 lần chạy phần tạo nhãn, không phải tổng thời gian pipeline. Toàn pipeline lần chạy cuối mất khoảng 12,19 giây trên môi trường đã ghi, gồm đọc CSV, làm sạch, tính RFM, khảo sát k, so sánh và ghi kết quả. Kết quả thời gian có thể biến động theo máy, tải hệ thống và cache.

K-Means có Silhouette cao hơn khoảng 0,2812 điểm và Davies–Bouldin thấp hơn khoảng 0,5580 điểm so với baseline trên cùng không gian đặc trưng. Đổi lại, thời gian tạo nhãn trung bình cao hơn và kết quả ít trực quan hơn quy tắc ngưỡng. K-Means tối ưu khoảng cách Euclid và có thể nhạy với ngoại lệ, lựa chọn biến đổi, thang đo và giả định cụm tương đối lồi/hình cầu. Baseline dễ truyền đạt nhưng việc chia quintile riêng lẻ không đảm bảo nhóm cuối cùng tách biệt về mặt hình học.

Các chỉ số nội tại chỉ hỗ trợ so sánh cấu trúc; không chứng minh K-Means sẽ tạo kết quả kinh doanh tốt hơn. Cần đánh giá khả năng hành động, chi phí triển khai và hiệu quả chiến dịch thực tế.

### 6.4. KPI toàn tập

| KPI | Giá trị thực tế | Đơn vị / phạm vi |
|---|---:|---|
| Silhouette K-Means | 0,4381 | Không đơn vị; 5.852 khách, k=2, không gian RFM chuẩn hóa |
| Silhouette baseline | 0,1568 | Không đơn vị; cùng khách và không gian chuẩn hóa, nhãn baseline |
| Tỷ lệ khách có ≥2 hóa đơn khác nhau | 72,35% | 5.852 khách trong toàn kỳ giao dịch sạch |
| Tỷ lệ mua lại qua 01/06/2011 | 52,91% | Khách mua trước mốc; tỷ lệ có mua từ mốc trở đi |
| Doanh thu dòng hàng hợp lệ | £17.068.808,72 | Tổng Quantity × Price, toàn bộ tập giao dịch sạch |
| Snapshot | 10/12/2011 | Ngày cuối dữ liệu sạch + 1 ngày |

Silhouette kiểm tra toàn tập bằng cùng hàm của scikit-learn; test KPI trên mẫu so khớp `silhouette_score`. Tỷ lệ quay lại đếm Invoice khác nhau, không phải số dòng sản phẩm. Doanh thu là tổng bán hàng dòng sản phẩm, không trừ chi phí, thuế, vận chuyển hay hoàn trả ngoài những gì đã loại khỏi tập.

### 6.5. Insight chính

1. **Tập trung doanh thu:** Champions là 39,90% khách nhưng chiếm 87,71% doanh thu sạch. Monetary trung bình của cụm là khoảng £6.411,38/khách.
2. **Nhóm quy mô lớn, giá trị quan sát thấp hơn:** At-risk/Lost chiếm 60,10% khách và 12,29% doanh thu. Recency trung bình 299,67 ngày, Frequency 2,08 hóa đơn và Monetary khoảng £596,60/khách.
3. **Mua lại qua thời gian:** 72,35% khách có ít nhất hai hóa đơn trong toàn kỳ; 52,91% khách đã mua trước 01/06/2011 tiếp tục xuất hiện trong tập giao dịch từ mốc đó trở đi.

Các kết quả là thống kê lịch sử gộp trên dữ liệu 2009–2011. Chúng không chứng minh nguyên nhân, không phản ánh tình trạng hiện tại và không cho biết khách có nhận chiến dịch hay không.

---

## 7. DASHBOARD VÀ KIỂM TRA TÍNH NHẤT QUÁN

Dashboard được xây dựng bằng Streamlit và Plotly. Các thành phần chính:

- Bộ lọc quốc gia.
- Khoảng ngày mua gần nhất.
- Phương pháp Baseline hoặc K-Means.
- Lọc phân khúc theo phương pháp đã chọn.
- Thẻ KPI: số khách, doanh thu GBP, Silhouette, tỷ lệ khách quay lại.
- Biểu đồ cột số khách và doanh thu theo phân khúc.
- Scatter Frequency–Monetary, có thể xem thông tin Recency/quốc gia.
- Heatmap Recency–Frequency.
- Đường chẩn đoán inertia và Silhouette theo k.
- Bảng so sánh phương pháp và bảng RFM trung bình.

KPI được tính lại trên tập khách sau lọc. Khi lọc chỉ còn một cụm hoặc số khách không đủ để tính Silhouette, dashboard hiển thị N/A thay vì điểm số không hợp lệ. Test kiểm tra sự nhất quán giữa KPI toàn tập dashboard và đầu ra pipeline đã chạy thành công.

**Hình cần chèn trước khi nộp:**

1. Hình 1 – Dashboard mặc định, tất cả quốc gia và hai phân khúc.
2. Hình 2 – Dashboard lọc Champions hoặc At-risk/Lost.
3. Hình 3 – Dashboard khi chọn Baseline.
4. Hình 4 – Terminal hiển thị KPI pipeline và/hoặc JSON log.
5. Hình 5 – Biểu đồ chọn k hoặc bảng so sánh.

Ảnh chụp cần được tạo từ phiên chạy thực tế và ghi chú điều kiện lọc. Không chèn ảnh minh họa giả lập thay cho minh chứng chạy.

---

## 8. ĐỀ XUẤT KINH DOANH

### 8.1. Chiến dịch theo phân khúc

| Phân khúc quan sát | Mục tiêu | Hành động đề xuất để thử nghiệm | KPI theo dõi |
|---|---|---|---|
| Champions | Duy trì quan hệ và giảm nguy cơ mất khách có giá trị cao | Early access, chăm sóc ưu tiên, ưu đãi có điều kiện; tránh giảm giá đại trà nếu không cần thiết | Tỷ lệ mua lại, doanh thu/khách, biên lợi nhuận, tần suất |
| Loyal / Potential | Tăng tần suất hoặc giá trị đơn | Gợi ý mua kèm, ưu đãi theo ngưỡng, chương trình thành viên | AOV, số hóa đơn/khách, tỷ lệ chuyển đổi |
| At-risk | Kích hoạt lại khách mua thưa hoặc đã lâu không mua | Email nhắc mua, ưu đãi cá nhân hóa, thử nghiệm nhóm thông điệp | Tỷ lệ phản hồi, tỷ lệ mua lại, doanh thu tăng thêm |
| Lost | Kiểm tra khả năng tái kích hoạt với chi phí thấp | Kênh chi phí thấp trước; hạn chế đầu tư voucher giá trị cao nếu không có tín hiệu phản hồi | Chi phí/khách quay lại, doanh thu tăng thêm, ROI thực |

Trong phân cụm hiện tại, K-Means chỉ tạo hai nhóm; vì vậy bảng chiến dịch nhiều hơn hai hàng là khung gợi ý nếu baseline, k khác hoặc quy tắc CRM bổ sung tách nhóm. Không được gán khách vào Loyal/Potential chỉ từ output K-Means k=2 hiện tại.

### 8.2. Minh họa độ nhạy chi phí

Để có ví dụ định lượng, pipeline giả định chi phí tiếp cận là £1,50/khách và tỷ lệ phản hồi là 1%, 3% hoặc 5%. Giá trị đơn trung bình được ước tính bằng doanh thu chia tổng số hóa đơn duy nhất. Doanh thu kỳ vọng = số khách × tỷ lệ phản hồi × giá trị đơn trung bình. ROI minh họa = (doanh thu kỳ vọng − chi phí chiến dịch) / chi phí chiến dịch.

| Phân khúc | Tỷ lệ phản hồi giả định | Chi phí ước tính | Doanh thu gộp kỳ vọng | ROI minh họa |
|---|---:|---:|---:|---:|
| At-risk/Lost (3.517 khách) | 1% | £5.275,50 | £10.071,61 | 90,91% |
| At-risk/Lost (3.517 khách) | 3% | £5.275,50 | £30.214,84 | 472,74% |
| At-risk/Lost (3.517 khách) | 5% | £5.275,50 | £50.358,06 | 854,56% |
| Champions (2.335 khách) | 1% | £3.502,50 | £11.939,85 | 240,90% |
| Champions (2.335 khách) | 3% | £3.502,50 | £35.819,56 | 922,69% |
| Champions (2.335 khách) | 5% | £3.502,50 | £59.699,26 | 1.604,48% |

**Cảnh báo diễn giải:** Đây không phải ROI tài chính thực tế. Tỷ lệ phản hồi và chi phí/khách là giả định; doanh thu là doanh thu gộp, không phải lợi nhuận tăng thêm; mô hình đơn giản chưa trừ giá vốn, phí gửi, voucher, hoàn trả, thuế hoặc doanh thu khách vốn sẽ mua dù không nhận chiến dịch. Con số cao trong bảng không đủ cơ sở để phê duyệt ngân sách. Bảng chỉ cho thấy kết quả phụ thuộc mạnh vào giả định phản hồi; cần thay bằng chi phí và biên lợi nhuận thật, sau đó chạy thử nghiệm có đối chứng.

### 8.3. Thiết kế kiểm chứng

1. Chọn nhóm khách đủ điều kiện và phân ngẫu nhiên thành nhóm nhận chiến dịch và nhóm đối chứng.
2. Định nghĩa trước cửa sổ đo lường, tiêu chí mua lại, doanh thu tăng thêm, chi phí tiếp cận và biên lợi nhuận.
3. So sánh tỷ lệ mua lại và lợi nhuận tăng thêm giữa hai nhóm; không quy toàn bộ doanh thu người nhận chiến dịch cho chiến dịch.
4. Theo dõi kết quả theo phân khúc, kênh và nội dung; dừng hoặc điều chỉnh nếu chi phí vượt ngưỡng.
5. Cập nhật RFM định kỳ hàng tháng/quý và theo dõi tỷ lệ khách chuyển nhóm.

---

## 9. HẠN CHẾ, RỦI RO VÀ HƯỚNG PHÁT TRIỂN

### 9.1. Giới hạn dữ liệu

- Dữ liệu thuộc giai đoạn 2009–2011, không đại diện hành vi mua hiện tại.
- Customer ID thiếu ở 22,77% dòng; nhóm khách không có mã có thể khác có hệ thống so với khách được định danh.
- Một khách hàng trong dữ liệu có thể là doanh nghiệp; không nên diễn giải mọi mã khách là một cá nhân.
- Không có chi phí marketing, giá vốn, margin và dữ liệu tiếp xúc chiến dịch; ROI thật không tính được.
- Không có ground truth phân khúc; không tính accuracy hoặc kết luận mô hình phân cụm “đúng” theo nhãn chuẩn.
- Phân tích gộp theo toàn kỳ có thể che giấu biến động mùa vụ hoặc thay đổi hành vi theo thời gian.
- Quy tắc stock code dựa vào danh sách mã dịch vụ/fee trong mã nguồn và có thể cần mở rộng.

### 9.2. Giới hạn phương pháp

- K-Means ưu tiên cụm theo khoảng cách Euclid; cụm có dạng không lồi, mật độ khác nhau hoặc kích thước rất lệch có thể không được mô tả tốt.
- k=2 có chỉ số nội tại tốt nhất trong dải đã thử nhưng làm giảm độ chi tiết kinh doanh. k=4 có Silhouette thấp hơn; cần cân bằng chất lượng hình học với khả năng hành động.
- Log1p giảm lệch nhưng không loại bỏ hoàn toàn ảnh hưởng của giá trị cực lớn.
- Baseline quintile và K-Means tạo số nhóm khác nhau (6 so với 2), làm khác biệt Silhouette chịu ảnh hưởng một phần từ số cụm và quy tắc nhãn.
- ARI baseline = 1 là do tính xác định; không phải bằng chứng baseline tốt hơn về tính ổn định thực tế.
- Thời gian benchmark trong bảng chỉ đo thao tác tạo nhãn, không so sánh tổng thời gian phát triển/tiền xử lý.
- Silhouette của lựa chọn lọc dashboard được tính lại theo tập con; nếu muốn so sánh trực tiếp giữa các bộ lọc, cần thống nhất scaler và quy tắc tính.

### 9.3. Hướng phát triển

1. Thu thập dữ liệu mới hơn, bổ sung lợi nhuận, chi phí khuyến mãi, lịch sử gửi/nhận thông điệp và phản hồi chiến dịch.
2. Theo dõi RFM theo nhiều snapshot để kiểm tra độ ổn định của phân khúc theo thời gian.
3. So sánh thêm k=3/4, Hierarchical hoặc Gaussian Mixture, giữ nguyên tập khách và không gian đặc trưng.
4. Định nghĩa chỉ số nghiệp vụ có thể kiểm chứng bằng A/B test, thay vì dùng Silhouette làm tiêu chuẩn duy nhất.
5. Thực hiện phân tích nhạy cảm với cách xử lý trả hàng, mã dịch vụ và khách có giá trị cực lớn.
6. Nếu cần tuyên bố khả năng mở rộng Big Data, thiết kế benchmark có kiểm soát trên Spark/Parquet hoặc hệ thống phân tán, tăng tải theo quy mô và báo cáo tài nguyên/độ trễ.
7. Bổ sung kiểm tra dashboard bằng ảnh và test tự động cho các tổ hợp bộ lọc thường dùng.

---

## 10. KẾT LUẬN

Đề tài đã xây dựng được pipeline có thể chạy lại trên Online Retail II, bao gồm kiểm tra dữ liệu, làm sạch, tách hóa đơn hủy, tính RFM theo ngày lịch, chuẩn hóa, baseline quintile, K-Means, đánh giá chỉ số, lưu log và dashboard. Trên 5.852 khách hàng còn lại, K-Means k=2 có Silhouette 0,4381 và Davies–Bouldin 0,8732; baseline sáu nhóm lần lượt đạt 0,1568 và 1,4312. Độ ổn định K-Means qua nhiều seed đạt ARI trung bình 0,9969. Bốn kiểm thử tự động đã chạy thành công, gồm test làm sạch, RFM, KPI và đối chiếu đầu ra.

Tỷ lệ khách có ít nhất hai hóa đơn là 72,35%; tỷ lệ mua lại qua mốc 01/06/2011 là 52,91%. Champions chiếm 39,90% khách và 87,71% doanh thu; At-risk/Lost chiếm 60,10% khách và 12,29% doanh thu. Những kết quả này trả lời các câu hỏi mô tả của đề tài nhưng không chứng minh quan hệ nhân quả hoặc hiệu quả của một chiến dịch.

Kết luận chính là dữ liệu RFM có thể hỗ trợ ưu tiên phân tích và thiết kế thử nghiệm CRM. Tuy nhiên, do dữ liệu cũ, thiếu Customer ID, không có nhãn chuẩn, không có chi phí/lợi nhuận thật và K-Means chỉ tạo hai cụm, doanh nghiệp cần xem phân khúc là tín hiệu tham khảo. Trước khi triển khai, cần cập nhật dữ liệu, xác thực nhãn với người dùng nghiệp vụ và đánh giá chiến dịch bằng A/B test có nhóm đối chứng.

---

## TÀI LIỆU THAM KHẢO

1. UCI Machine Learning Repository. *Online Retail II*. <https://archive.ics.uci.edu/dataset/502/online+retail+ii>. Truy cập: [điền ngày truy cập].
2. Kaggle. *Online Retail II*. <https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci>. Truy cập: [điền ngày truy cập].
3. scikit-learn Developers. *Clustering performance evaluation*. <https://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation>.
4. scikit-learn Developers. *KMeans*. <https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html>.
5. Tài liệu giao đề CO4033, *Bộ 17 đề tài bài tập lớn – Phân tích dữ liệu lớn và Trí tuệ kinh doanh*, đề tài 04 và yêu cầu chung.
6. Mã nguồn và kết quả thực nghiệm của nhóm trong thư mục dự án: `src/`, `tests/`, `dashboard/`, `reports/`.

---

## PHỤ LỤC A. ĐẦU RA CÓ THỂ ĐỐI CHIẾU

| Tệp | Nội dung |
|---|---|
| `reports/dataset_profile.json` | Kích thước và phạm vi ngày dữ liệu |
| `reports/data_dictionary.csv` | Kiểu trường, ý nghĩa và tỷ lệ thiếu |
| `reports/quality_before_after.csv` | Dòng, khách, hóa đơn, thiếu/trùng theo từng bước |
| `reports/cluster_diagnostics.csv` | Inertia, Silhouette, Davies–Bouldin theo k |
| `reports/comparison.csv` | So sánh baseline và K-Means |
| `reports/kpi_summary.json` | KPI toàn tập |
| `reports/kmeans_cluster_profiles.csv` | RFM trung bình theo cụm |
| `reports/segment_insights.csv` | Quy mô và doanh thu theo cụm |
| `reports/campaign_sensitivity.csv` | Ước tính theo giả định phản hồi |
| `reports/hardware.json` | Cấu hình môi trường chạy |
| `reports/logs/` | Số dòng và thời gian từng giai đoạn |
| `data/processed/customer_segments.csv` | RFM và nhãn từng khách |
| `data/processed/clean_transactions.csv` | Giao dịch sạch |
| `data/processed/cancellations.csv` | Hóa đơn hủy được tách riêng |

---

## PHỤ LỤC B. PHÂN CÔNG VÀ KHAI BÁO CÔNG CỤ

### B.1. Phân công thành viên

| Thành viên | Công việc thực hiện | Tỷ lệ đóng góp / minh chứng |
|---|---|---|
| [Thành viên 1] | [Khảo sát dữ liệu / nguồn] | [Điền] |
| [Thành viên 2] | [Làm sạch / pipeline / test] | [Điền] |
| [Thành viên 3] | [Phân tích / dashboard] | [Điền] |
| [Thành viên 4] | [Báo cáo / đề xuất / demo] | [Điền] |
| [Thành viên 5, nếu có] | [Điền] | [Điền] |

### B.2. Khai báo sử dụng AI

Theo yêu cầu liêm chính học thuật của tài liệu giao đề, nhóm cần ghi rõ công cụ AI và mục đích sử dụng. Mẫu cần được nhóm chỉnh sửa cho chính xác:

> Nhóm có sử dụng trợ lý AI để hỗ trợ rà soát yêu cầu, gợi ý cấu trúc báo cáo và diễn đạt bản nháp. Nhóm đã tự kiểm tra mã nguồn, chạy pipeline và kiểm thử, đối chiếu các số liệu với tệp đầu ra, đồng thời chịu trách nhiệm về nội dung cuối cùng. Các phần nội dung, phân tích và nhận xét được nhóm xác minh và hiệu chỉnh trước khi nộp.

Nếu cách sử dụng thực tế khác, cần thay nội dung mẫu bằng khai báo đúng; không giữ nguyên nếu không phản ánh quá trình làm việc của nhóm.
