from django.db.models import Q
import random
from .action import get_id_list_from_str
from .models import *
import jieba
from collections import defaultdict

# 内置停用词列表（可根据需求扩展）
STOPWORDS = {
    "的", "是", "在", "了", "啊", "吗", "和", "有", "就", "这",
    "推荐", "什么", "怎么", "如何", "哪些", "求", "吧", "呢"
}

def get_keyword_from_book(book_history):
    books = Book.objects.filter(ISBN__in=book_history).only('ISBN', 'BookTitle', 'keyword')

    word_freq = defaultdict(int)

    for book in books:
        # 处理书名分词
        title_words = jieba.lcut(book.BookTitle)

        # 处理关键词（假设keywords是逗号分隔的字符串）
        if book.keyword:
            keyword_list = [kw.strip() for kw in book.keyword.split(',')]
        else:
            keyword_list = []

        # 合并所有词汇
        all_words = title_words + keyword_list

        # 统计词频（过滤停用词和单字）
        for word in all_words:
            word = word.lower()  # 英文转小写
            if (len(word) > 1 and
                    word not in STOPWORDS and
                    not word.isdigit()):
                word_freq[word] += 1

    # 按词频降序排序
    return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

def get_keyword_from_search(search_history):
    keyword_counts = defaultdict(int)

    # 处理每个搜索词
    for query in search_history:
        # 中文分词
        words = jieba.lcut_for_search(str(query))
        for word in words:
            # 统一小写处理（兼容中英文）
            word = word.strip().lower()
            # 过滤规则：长度>1、非停用词、非数字
            if (len(word) > 1 and
                word not in STOPWORDS and
                not word.isdigit()):
                keyword_counts[word] += 1

    # 按词频排序
    return sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)

def get_interesting(user):
    """
    :param:
    user: 用户
    :return:
    fond: 生成一些词条，然后计算权重，分析用户对那些类别的书籍感兴趣，用 list存储

    分析History,当中通过book_history, search_history中存储的信息，分析关键词，并通过出现评率计算要推荐书籍类型出现的权重
    """
    history = History.objects.get(user=user)
    book_history = get_id_list_from_str(history.book_history)
    search_history = get_id_list_from_str(history.search_history)
    keyword = get_keyword_from_book(book_history) + get_keyword_from_search(search_history)
    return keyword


def generate_recommend(userID, num_recommendations=50):
    # 获取用户及其兴趣权重
    user = User.objects.get(userID=userID)
    combined_weights = get_combined_weights(user)

    # 构造概率分布
    total_weight = sum(weight for _, weight in combined_weights)
    if total_weight <= 0:
        return get_fallback_recommendations()

    # 预加载所有相关书籍（优化数据库查询）
    all_keywords = [kw for kw, _ in combined_weights]
    books_mapping = get_books_by_keywords(all_keywords)

    # 轮盘赌选择算法生成推荐
    recommendations = []
    seen_books = set()
    for _ in range(num_recommendations * 2):  # 扩大选择池避免重复
        # 按权重随机选择关键词
        selected_keyword = weighted_random_choice(combined_weights, total_weight)
        if not selected_keyword:
            continue

        # 获取候选书籍并随机选择
        candidate_books = books_mapping.get(selected_keyword, [])
        if candidate_books:
            book = random.choice(candidate_books)
            if book.ISBN not in seen_books:
                recommendations.append(book)
                seen_books.add(book.ISBN)
                if len(recommendations) >= num_recommendations:
                    break

    # 补足推荐数量（如果不足）
    if len(recommendations) < num_recommendations:
        fallback = get_fallback_recommendations(exclude=seen_books)
        recommendations.extend(fallback[:num_recommendations - len(recommendations)])
    print(recommendations)
    return recommendations[:num_recommendations]


def get_combined_weights(user):
    """合并用户及其关注者的兴趣权重"""
    combined = defaultdict(float)

    # 主用户兴趣（2倍权重）
    for word, weight in get_interesting(user):
        combined[word] += weight * 2.0

    # 关注用户兴趣（1倍权重）
    ups = get_id_list_from_str(Group.objects.get(user=user).ups)
    for up in ups[:10]:  # 限制最多10个关注
        up_user = User.objects.get(userID=up)
        for word, weight in get_interesting(up_user):
            combined[word] += weight

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)


def get_books_by_keywords(keywords, batch_size=1000):
    """批量获取关键词相关的书籍（优化查询）"""
    query = Q()
    for keyword in keywords:
        query |= Q(keyword__icontains=keyword) | Q(BookTitle__icontains=keyword)

    books = Book.objects.filter(query)[:batch_size]

    # 构建关键词到书籍的映射
    mapping = defaultdict(list)
    for book in books:
        # 提取书籍关键词（标题分词+关键词字段）
        title_words = jieba.lcut(book.BookTitle)
        keywords = title_words + book.keyword.split(',')
        for word in set(keywords):
            mapping[word].append(book)

    return mapping


def weighted_random_choice(weights, total_weight=None):
    """轮盘赌选择算法"""
    if not weights:
        return None

    total = total_weight or sum(w for _, w in weights)
    if total <= 0:
        return None

    rand = random.uniform(0, total)
    cumulative = 0
    for word, weight in weights:
        cumulative += weight
        if rand <= cumulative:
            return word
    return weights[-1][0]


def get_fallback_recommendations(exclude=None, num=50):
    """获取后备推荐（热门书籍）"""
    query = Book.objects.all()
    if exclude:
        query = query.exclude(ISBN__in=exclude)
    return list(query.order_by('-score')[:num])