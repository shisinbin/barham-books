from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Post
from taggit.models import Tag
from .forms import SearchForm

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def post_list(request, tag_slug=None):
	object_list = Post.published.all()
	tag = None
	if tag_slug:
		tag = get_object_or_404(Tag, slug=tag_slug)
		object_list = object_list.filter(tags__in=[tag])
	
	paginator = Paginator(object_list, 2)
	page = request.GET.get('page')
	paged_posts = paginator.get_page(page)

	# paginator = Paginator(object_list, 3) # 3 posts in each page
	# page = request.GET.get('page')
	# try:
	# 	posts = paginator.page(page)
	# except PageNotAnInteger:
	# 	# if page is not an integer deliver the first page
	# 	posts = paginator.page(1)
	# except EmptyPage:
	# 	# if page is out of range deliver last page of results
	# 	posts = paginator.page(paginator.num_pages)

	form = SearchForm()
	context = {
		'page': page,
		'posts': paged_posts,
		'tag': tag,
		'form': form,
	}
	return render(request, 'blog/post_list.html', context)

@staff_member_required
def post_detail(request, year, month, day, post):
	post = get_object_or_404(Post, slug=post,
								   status='published',
								   publish__year=year,
								   publish__month=month,
								   publish__day=day)

	context = {
		'post': post,
	}

	return render(request, 'blog/post_detail.html', context)

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

@staff_member_required
def post_search(request):
	form = SearchForm()
	query = None
	results = []
	if 'query' in request.GET:
		form = SearchForm(request.GET)
		if form.is_valid():
			query = form.cleaned_data['query']
			search_vector = SearchVector('title', weight='A') + \
							SearchVector('body', weight='B')
			search_query = SearchQuery(query)
			results = Post.published.annotate(
				search=search_vector,
				rank=SearchRank(search_vector, search_query)
				).filter(rank__gte=0.3).order_by('-rank')
	context = {
		'form': form,
		'query': query,
		'results': results,
	}
	return render(request, 'blog/search.html', context)