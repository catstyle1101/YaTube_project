from django.urls import path

from . import views

app_name = 'posts'


urlpatterns = [
    path('group/<slug:slug>/', views.GroupPostsView.as_view(),
         name='group_list'),
    path('profile/<str:username>/', views.ProfileView.as_view(),
         name='profile'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(),
         name='post_detail'),
    path('create/', views.PostCreateView.as_view(),
         name='post_create'),
    path('posts/<int:pk>/edit/', views.PostEditView.as_view(),
         name='post_edit'),
    path('posts/<int:pk>/comment/', views.AddCommentView.as_view(),
         name='add_comment'),
    path('follow/', views.FollowingListView.as_view(),
         name='follow_index'),
    path('profile/<str:username>/follow/', views.FollowAuthor.as_view(),
         name='profile_follow'),
    path('profile/<str:username>/unfollow/', views.UnFollowAuthor.as_view(),
         name='profile_unfollow'),
    path('', (views.Index.as_view()),
         name='index_page'),
]
