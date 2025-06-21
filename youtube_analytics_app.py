import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
from io import BytesIO
import os
import traceback

from youtube_service import YouTubeService
from data_utils import DataProcessor
from database import DatabaseManager

# Page configuration
st.set_page_config(page_title="YouTube Video Search Analytics",
                   page_icon="🔍",
                   layout="wide",
                   initial_sidebar_state="expanded")


def main():
    st.title("📊 YouTube Analytics Dashboard")
    st.markdown(
        "Analyze YouTube channels and search for videos based on your criteria"
    )

    # Initialize database with retry
    if 'db_manager' not in st.session_state:
        try:
            db = DatabaseManager()
            st.session_state['db_manager'] = db
            st.success("Database connected successfully")
        except Exception as e:
            st.warning(f"Database connection failed: {str(e)}")
            st.info("The app will continue to work without database features")
            st.session_state['db_manager'] = None

    # Create tabs
    tab1, tab2, tab3 = st.tabs(
        ["📺 Channel Analysis", "🔍 Video Search", "📚 Search History"])

    with tab1:
        channel_analysis_tab()

    with tab2:
        video_search_tab()

    with tab3:
        search_history_tab()


def channel_analysis_tab():
    st.header("📺 Channel Analytics")
    st.markdown("Analyze videos from a specific YouTube channel")

    # Sidebar for channel analysis
    with st.sidebar:
        st.header("⚙️ Channel Configuration")

       

        # Channel ID input
        channel_id = st.text_input(
            "Channel ID",
            help="Enter the YouTube Channel ID (e.g., UCxxxxxx)",
            placeholder="UCxxxxxx",
            key="channel_id_input")

        # Number of videos slider
        max_videos = st.slider("Number of Recent Videos",
                               min_value=1,
                               max_value=50,
                               value=10,
                               help="Select how many recent videos to analyze",
                               key="channel_max_videos")

        # Date filtering options
        st.subheader("📅 Date Filtering")
        date_filter_option = st.selectbox("Filter by Date", [
            "All Videos", "Last 30 Days", "Last 90 Days", "Last Year",
            "Custom Range"
        ],
                                          key="channel_date_filter")

        start_date = None
        end_date = None

        if date_filter_option == "Custom Range":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date",
                                           key="channel_start_date")
            with col2:
                end_date = st.date_input("End Date", key="channel_end_date")
        elif date_filter_option == "Last 30 Days":
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
        elif date_filter_option == "Last 90 Days":
            start_date = datetime.now() - timedelta(days=90)
            end_date = datetime.now()
        elif date_filter_option == "Last Year":
            start_date = datetime.now() - timedelta(days=365)
            end_date = datetime.now()

        # Upload date filters
        st.subheader("📅 Upload Date Filters")
        upload_filter_option = st.selectbox("Filter by Upload Date", [
            "All Videos", "Last 7 Days", "Last 30 Days", "Last 90 Days",
            "Last Year", "Custom Range"
        ],
                                            key="channel_upload_filter")

        upload_start_date = None
        upload_end_date = None

        if upload_filter_option == "Custom Range":
            col1, col2 = st.columns(2)
            with col1:
                upload_start_date = st.date_input(
                    "Upload Start Date", key="channel_upload_start_date")
            with col2:
                upload_end_date = st.date_input("Upload End Date",
                                                key="channel_upload_end_date")
        elif upload_filter_option == "Last 7 Days":
            upload_start_date = datetime.now() - timedelta(days=7)
            upload_end_date = datetime.now()
        elif upload_filter_option == "Last 30 Days":
            upload_start_date = datetime.now() - timedelta(days=30)
            upload_end_date = datetime.now()
        elif upload_filter_option == "Last 90 Days":
            upload_start_date = datetime.now() - timedelta(days=90)
            upload_end_date = datetime.now()
        elif upload_filter_option == "Last Year":
            upload_start_date = datetime.now() - timedelta(days=365)
            upload_end_date = datetime.now()

        # Display options
        st.subheader("🎨 Display Options")
        show_thumbnails_channel = st.checkbox("Show Video Thumbnails",
                                              value=True,
                                              key="channel_thumbnails")

        # Analyze button
        analyze_button = st.button("🔍 Analyze Channel",
                                   type="primary",
                                   key="channel_analyze")

    # Main content area for channel analysis

    if not channel_id:
        st.warning("⚠️ Please enter a Channel ID in the sidebar.")
        st.info("""
        **How to find a Channel ID:**
        1. Go to the YouTube channel
        2. Look at the URL - if it contains `/channel/`, copy the ID after it
        3. If the URL contains `/c/` or `/user/`, use online tools to convert to Channel ID
        4. Channel IDs typically start with 'UC' followed by 22 characters
        """)
        return

    if analyze_button or 'channel_analysis_data' in st.session_state:
        if analyze_button:
            # Initialize services
            youtube_service = YouTubeService()
            data_processor = DataProcessor()

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Step 1: Get channel info
                status_text.text("Fetching channel information...")
                progress_bar.progress(20)

                channel_info = youtube_service.get_channel_info(channel_id)
                if not channel_info:
                    st.error(
                        "❌ Invalid Channel ID or channel not found. Please check your API key and Channel ID."
                    )
                    return

                # Step 2: Get videos
                status_text.text("Fetching recent videos...")
                progress_bar.progress(50)

                videos = youtube_service.get_channel_videos(
                    channel_id, max_videos)
                if not videos:
                    st.error("❌ No videos found for this channel.")
                    return

                # Step 3: Process data
                status_text.text("Processing video data...")
                progress_bar.progress(80)

                # Filter by original date range if specified
                if start_date and end_date:
                    videos = data_processor.filter_videos_by_date(
                        videos, start_date, end_date)

                # Filter by upload date if specified
                if upload_start_date and upload_end_date:
                    videos = data_processor.filter_videos_by_date(
                        videos, upload_start_date, upload_end_date)

                # Calculate metrics
                processed_data = data_processor.calculate_metrics(
                    videos, channel_info['subscriber_count'])

                # Save to database if available
                if st.session_state.get('db_manager'):
                    try:
                        search_history_id = st.session_state[
                            'db_manager'].save_search_history(
                                search_query=
                                f"Channel: {channel_info['title']}",
                                search_type='channel',
                                channel_id=channel_id,
                                total_results=len(videos))

                        # Convert processed_data to list of dicts for saving
                        videos_for_db = processed_data.to_dict('records')
                        st.session_state['db_manager'].save_video_results(
                            search_history_id, videos_for_db)
                        st.info("Results saved to database")
                    except Exception as db_error:
                        st.warning(
                            "Database save failed - continuing without saving")
                        # Reset database manager if connection is broken
                        st.session_state['db_manager'] = None

                # Store in session state
                st.session_state['channel_analysis_data'] = {
                    'channel_info': channel_info,
                    'processed_data': processed_data,
                    'show_thumbnails': show_thumbnails_channel
                }

                progress_bar.progress(100)
                status_text.text("Analysis complete!")

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.error("Please check:")
                st.error("- Your YouTube API key is valid")
                st.error("- The Channel ID is correct")
                st.error("- You have sufficient API quota")
                with st.expander("Technical Details"):
                    st.code(traceback.format_exc())
                return

        # Display channel analysis results
        if 'channel_analysis_data' in st.session_state:
            data = st.session_state['channel_analysis_data']
            channel_info = data['channel_info']
            df = data['processed_data']
            show_thumbnails = data['show_thumbnails']

            # Channel overview
            st.header(f"📺 {channel_info['title']}")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if channel_info.get('subscriber_count_hidden'):
                    st.metric("Subscribers", "Hidden")
                else:
                    st.metric("Subscribers",
                              f"{channel_info['subscriber_count']:,}")
            with col2:
                st.metric("Total Videos Analyzed", len(df))
            with col3:
                if channel_info['subscriber_count'] > 0:
                    avg_views_per_sub = df['views_per_subscriber'].mean()
                    st.metric("Avg Views/Subscriber",
                              f"{avg_views_per_sub:.3f}")
                else:
                    avg_views = df['view_count'].mean()
                    st.metric("Avg Views per Video", f"{avg_views:,.0f}")
            with col4:
                total_views = df['view_count'].sum()
                st.metric("Total Views (Analyzed)", f"{total_views:,}")

            # Visualization
            st.header("📊 Views per Subscriber Analysis")

            # Bar chart
            fig = px.bar(
                df.head(15),  # Show top 15 for better readability
                x='views_per_subscriber',
                y='title',
                orientation='h',
                title='Top Videos by Views per Subscriber Ratio',
                labels={
                    'views_per_subscriber': 'Views per Subscriber',
                    'title': 'Video Title'
                },
                hover_data=['view_count', 'published_date'])
            fig.update_layout(height=600,
                              yaxis={'categoryorder': 'total ascending'},
                              showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # Interactive data table
            st.header("📋 Detailed Video Analysis")

            # Prepare display dataframe
            display_df = df.copy()

            if show_thumbnails:
                # Add thumbnail column
                display_df['Thumbnail'] = display_df['thumbnail_url'].apply(
                    lambda url: url if url else "")

            # Format columns for display
            display_df['Views'] = display_df['view_count'].apply(
                lambda x: f"{x:,}")
            display_df['Views/Subscriber'] = display_df[
                'views_per_subscriber'].apply(lambda x: f"{x:.4f}")
            display_df['Published'] = pd.to_datetime(
                display_df['published_date']).dt.strftime('%Y-%m-%d')
            display_df['Upload Date'] = pd.to_datetime(
                display_df['published_date']).dt.strftime('%Y-%m-%d')
            display_df['Duration'] = display_df['duration']

            # Select columns for display
            if show_thumbnails:
                display_columns = [
                    'Thumbnail', 'title', 'Views', 'Views/Subscriber',
                    'Upload Date', 'Duration'
                ]
                column_config = {
                    'Thumbnail':
                    st.column_config.ImageColumn('Thumbnail', width='small'),
                    'title':
                    st.column_config.TextColumn('Title', width='large'),
                    'Views':
                    st.column_config.TextColumn('Views'),
                    'Views/Subscriber':
                    st.column_config.TextColumn('Views/Subscriber'),
                    'Upload Date':
                    st.column_config.TextColumn('Upload Date'),
                    'Duration':
                    st.column_config.TextColumn('Duration')
                }
            else:
                display_columns = [
                    'title', 'Views', 'Views/Subscriber', 'Upload Date',
                    'Duration'
                ]
                column_config = {
                    'title':
                    st.column_config.TextColumn('Title', width='large'),
                    'Views':
                    st.column_config.TextColumn('Views'),
                    'Views/Subscriber':
                    st.column_config.TextColumn('Views/Subscriber'),
                    'Upload Date':
                    st.column_config.TextColumn('Upload Date'),
                    'Duration':
                    st.column_config.TextColumn('Duration')
                }

            # Display interactive table
            st.dataframe(display_df[display_columns],
                         column_config=column_config,
                         hide_index=True,
                         use_container_width=True)

            # Download CSV button
            st.subheader("💾 Export Data")

            # Prepare CSV data
            csv_df = df[[
                'title', 'view_count', 'views_per_subscriber',
                'published_date', 'duration', 'video_url'
            ]].copy()
            csv_df.columns = [
                'Title', 'View Count', 'Views per Subscriber',
                'Published Date', 'Duration', 'Video URL'
            ]

            csv_buffer = BytesIO()
            csv_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=
                f"youtube_analytics_{channel_info['title'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="Download the analysis results as a CSV file",
                key="channel_download")


def video_search_tab():
    st.header("🔍 Video Search Analytics")
    st.markdown("Search and analyze YouTube videos based on your criteria")

    # Sidebar for video search
    with st.sidebar:
        st.header("⚙️ Search Configuration")

        # Fixed API Key
        api_key = "AIzaSyAT-36ZFqzACrcnb80zbz3yaMDANaa9EQ4"

        # Search query input
        search_query = st.text_input(
            "Search Keywords",
            help=
            "Enter keywords to search for videos (e.g., 'python tutorial', '음악', '요리')",
            placeholder="Enter search terms...",
            key="search_query_input")

        # Search options
        st.subheader("🎯 Search Filters")

        # Channel filters
        st.markdown("**Channel Performance Filters:**")

        col1, col2 = st.columns(2)

        with col1:
            min_views = st.number_input(
                "Min Video Views",
                min_value=0,
                value=1000,
                step=100,
                help="Filter videos with at least this many views",
                key="search_min_views")

        with col2:
            max_subscribers = st.number_input(
                "Max Channel Subscribers",
                min_value=0,
                value=100000,
                step=1000,
                help=
                "Filter videos from channels with at most this many subscribers",
                key="search_max_subscribers")

        # Video properties
        st.markdown("**Video Properties:**")

        col1, col2 = st.columns(2)

        with col1:
            max_results = st.slider("Number of Results",
                                    min_value=5,
                                    max_value=50,
                                    value=25,
                                    help="Maximum number of videos to return",
                                    key="search_max_results")

        with col2:
            video_duration = st.selectbox("Video Duration", [
                "Any", "Short (< 4 min)", "Medium (4-20 min)",
                "Long (> 20 min)"
            ],
                                          key="search_duration")

        # Date filters
        st.subheader("📅 Date Filters")

        published_filter = st.selectbox("Published After", [
            "Any Time", "Last Hour", "Today", "This Week", "This Month",
            "This Year"
        ],
                                        key="search_published_filter")

        # Sort options
        st.subheader("📊 Sort Options")

        sort_by = st.selectbox(
            "Sort By", ["Relevance", "Upload Date", "View Count", "Rating"],
            key="search_sort_by")

        # Display options
        st.subheader("🎨 Display Options")
        show_thumbnails_search = st.checkbox("Show Video Thumbnails",
                                             value=True,
                                             key="search_thumbnails")

        # Search button
        search_button = st.button("🔍 Search Videos",
                                  type="primary",
                                  key="search_videos_btn")

    # Main content area for video search

    if not search_query:
        st.warning("⚠️ Please enter search keywords in the sidebar.")
        st.info("""
        **Search Tips:**
        - Use specific keywords for better results
        - Try different languages (e.g., '음악', 'music', 'música')
        - Combine terms with spaces (e.g., 'python tutorial beginners')
        - Use quotes for exact phrases
        """)
        return

    if search_button or 'search_results_data' in st.session_state:
        if search_button:
            # Initialize services
            youtube_service = YouTubeService(api_key)
            data_processor = DataProcessor()

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Prepare search parameters
                status_text.text("Preparing search parameters...")
                progress_bar.progress(10)

                # Duration mapping
                duration_map = {
                    "Any": None,
                    "Short (< 4 min)": "short",
                    "Medium (4-20 min)": "medium",
                    "Long (> 20 min)": "long"
                }
                duration_param = duration_map[video_duration]

                # Published after mapping
                published_after = None
                if published_filter == "Last Hour":
                    published_after = datetime.now() - timedelta(hours=1)
                elif published_filter == "Today":
                    published_after = datetime.now() - timedelta(days=1)
                elif published_filter == "This Week":
                    published_after = datetime.now() - timedelta(weeks=1)
                elif published_filter == "This Month":
                    published_after = datetime.now() - timedelta(days=30)
                elif published_filter == "This Year":
                    published_after = datetime.now() - timedelta(days=365)

                # Sort mapping
                sort_map = {
                    "Relevance": "relevance",
                    "Upload Date": "date",
                    "View Count": "viewCount",
                    "Rating": "rating"
                }
                order_param = sort_map[sort_by]

                # Search for videos
                status_text.text("Searching for videos...")
                progress_bar.progress(30)

                videos = youtube_service.search_videos(
                    query=search_query,
                    max_results=max_results,
                    duration=duration_param,
                    published_after=published_after,
                    order=order_param)

                if not videos:
                    st.error(
                        "❌ No videos found for your search criteria. Try different keywords or filters."
                    )
                    return

                # Process search results
                status_text.text("Processing search results...")
                progress_bar.progress(60)

                # Calculate metrics for search results
                processed_data = data_processor.calculate_search_metrics(
                    videos)

                # Filter by view count and subscriber count
                status_text.text("Applying filters...")
                progress_bar.progress(80)

                # Apply view count filter
                if min_views > 0:
                    processed_data = processed_data[
                        processed_data['view_count'] >= min_views]

                # Apply subscriber count filter (if available)
                if max_subscribers > 0 and 'channel_subscriber_count' in processed_data.columns:
                    processed_data = processed_data[
                        processed_data['channel_subscriber_count'] <=
                        max_subscribers]

                if len(processed_data) == 0:
                    st.warning(
                        "⚠️ No videos found matching your filters. Try adjusting the criteria."
                    )
                    return

                # Save to database if available
                if st.session_state.get('db_manager'):
                    try:
                        search_history_id = st.session_state[
                            'db_manager'].save_search_history(
                                search_query=search_query,
                                search_type='video_search',
                                total_results=len(processed_data),
                                min_views=min_views,
                                max_subscribers=max_subscribers)

                        # Convert processed_data to list of dicts for saving
                        videos_for_db = processed_data.to_dict('records')
                        st.session_state['db_manager'].save_video_results(
                            search_history_id, videos_for_db)
                        st.info("Search results saved to database")
                    except Exception as db_error:
                        st.warning(
                            "Database save failed - continuing without saving")
                        # Reset database manager if connection is broken
                        st.session_state['db_manager'] = None

                # Store in session state
                st.session_state['search_results_data'] = {
                    'processed_data': processed_data,
                    'search_query': search_query,
                    'show_thumbnails': show_thumbnails_search,
                    'search_params': {
                        'min_views': min_views,
                        'max_subscribers': max_subscribers,
                        'duration': video_duration,
                        'published_filter': published_filter,
                        'sort_by': sort_by
                    }
                }

                progress_bar.progress(100)
                status_text.text("Search complete!")

            except Exception as e:
                st.error(f"❌ Error during search: {str(e)}")
                st.error("Please check:")
                st.error("- Your search keywords are valid")
                st.error("- Your YouTube API key is working")
                st.error("- You have sufficient API quota")
                with st.expander("Technical Details"):
                    st.code(traceback.format_exc())
                return

        # Display search results
        if 'search_results_data' in st.session_state:
            data = st.session_state['search_results_data']
            df = data['processed_data']
            search_query = data['search_query']
            show_thumbnails = data['show_thumbnails']
            search_params = data['search_params']

            # Search results overview
            st.header(f"🔍 Search Results for: '{search_query}'")

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Videos Found", len(df))
            with col2:
                avg_views = df['view_count'].mean()
                st.metric("Average Views", f"{avg_views:,.0f}")
            with col3:
                total_views = df['view_count'].sum()
                st.metric("Total Views", f"{total_views:,}")
            with col4:
                unique_channels = df['channel_title'].nunique(
                ) if 'channel_title' in df.columns else 0
                st.metric("Unique Channels", unique_channels)

            # Visualization
            st.header("📊 Search Results Analysis")

            # Views distribution
            fig = px.histogram(df,
                               x='view_count',
                               nbins=20,
                               title='Distribution of Video Views',
                               labels={
                                   'view_count': 'View Count',
                                   'count': 'Number of Videos'
                               })
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # Interactive data table
            st.header("📋 Detailed Video Results")

            # Add filters for the results table
            col1, col2 = st.columns(2)

            with col1:
                # Subscriber count range filter
                if 'channel_subscriber_count' in df.columns and df[
                        'channel_subscriber_count'].notna().any():
                    min_subs = int(df['channel_subscriber_count'].min())
                    max_subs = int(df['channel_subscriber_count'].max())

                    # Ensure min and max are different for slider
                    if min_subs == max_subs:
                        max_subs = min_subs + 1

                    sub_range = st.slider(
                        "Channel Subscriber Range",
                        min_value=min_subs,
                        max_value=max_subs,
                        value=(min_subs, max_subs),
                        key="subscriber_range_filter",
                        help="Filter by channel subscriber count")
                else:
                    sub_range = None
                    st.write("Subscriber data not available")

            with col2:
                # View count range filter
                min_views_filter = int(df['view_count'].min())
                max_views_filter = int(df['view_count'].max())

                # Ensure min and max are different for slider
                if min_views_filter == max_views_filter:
                    max_views_filter = min_views_filter + 1

                view_range = st.slider("Video View Count Range",
                                       min_value=min_views_filter,
                                       max_value=max_views_filter,
                                       value=(min_views_filter,
                                              max_views_filter),
                                       key="view_range_filter",
                                       help="Filter by video view count")

            # Apply filters
            filtered_df = df.copy()

            # Subscriber count filter
            if sub_range and 'channel_subscriber_count' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['channel_subscriber_count'] >= sub_range[0]) &
                    (filtered_df['channel_subscriber_count'] <= sub_range[1])]

            # View count filter
            filtered_df = filtered_df[
                (filtered_df['view_count'] >= view_range[0])
                & (filtered_df['view_count'] <= view_range[1])]

            # Prepare display dataframe
            filtered_display_df = filtered_df.copy()

            if show_thumbnails:
                # Add thumbnail column
                filtered_display_df['Thumbnail'] = filtered_display_df[
                    'thumbnail_url'].apply(lambda url: url if url else "")

            # Format columns for display
            filtered_display_df['Views'] = filtered_display_df[
                'view_count'].apply(lambda x: f"{x:,}")
            filtered_display_df['Channel'] = filtered_display_df[
                'channel_title'] if 'channel_title' in filtered_display_df.columns else "Unknown"
            filtered_display_df['Published'] = pd.to_datetime(
                filtered_display_df['published_date']).dt.strftime('%Y-%m-%d')
            filtered_display_df['Duration'] = filtered_display_df['duration']

            # Add subscriber info if available
            if 'channel_subscriber_count' in filtered_display_df.columns:
                filtered_display_df['Subscribers'] = filtered_display_df[
                    'channel_subscriber_count'].apply(
                        lambda x: f"{int(x):,}" if pd.notna(x) else "Unknown")

                # Select columns for display
                if show_thumbnails:
                    display_columns = [
                        'Thumbnail', 'title', 'Channel', 'Views',
                        'Subscribers', 'Published', 'Duration'
                    ]
                    column_config = {
                        'Thumbnail':
                        st.column_config.ImageColumn('Thumbnail',
                                                     width='small'),
                        'title':
                        st.column_config.TextColumn('Title', width='large'),
                        'Channel':
                        st.column_config.TextColumn('Channel'),
                        'Views':
                        st.column_config.TextColumn('Views'),
                        'Subscribers':
                        st.column_config.TextColumn('Subscribers'),
                        'Published':
                        st.column_config.TextColumn('Published'),
                        'Duration':
                        st.column_config.TextColumn('Duration')
                    }
                else:
                    display_columns = [
                        'title', 'Channel', 'Views', 'Subscribers',
                        'Published', 'Duration'
                    ]
                    column_config = {
                        'title':
                        st.column_config.TextColumn('Title', width='large'),
                        'Channel':
                        st.column_config.TextColumn('Channel'),
                        'Views':
                        st.column_config.TextColumn('Views'),
                        'Subscribers':
                        st.column_config.TextColumn('Subscribers'),
                        'Published':
                        st.column_config.TextColumn('Published'),
                        'Duration':
                        st.column_config.TextColumn('Duration')
                    }
            else:
                # Select columns for display without subscriber info
                if show_thumbnails:
                    display_columns = [
                        'Thumbnail', 'title', 'Channel', 'Views', 'Published',
                        'Duration'
                    ]
                    column_config = {
                        'Thumbnail':
                        st.column_config.ImageColumn('Thumbnail',
                                                     width='small'),
                        'title':
                        st.column_config.TextColumn('Title', width='large'),
                        'Channel':
                        st.column_config.TextColumn('Channel'),
                        'Views':
                        st.column_config.TextColumn('Views'),
                        'Published':
                        st.column_config.TextColumn('Published'),
                        'Duration':
                        st.column_config.TextColumn('Duration')
                    }
                else:
                    display_columns = [
                        'title', 'Channel', 'Views', 'Published', 'Duration'
                    ]
                    column_config = {
                        'title':
                        st.column_config.TextColumn('Title', width='large'),
                        'Channel':
                        st.column_config.TextColumn('Channel'),
                        'Views':
                        st.column_config.TextColumn('Views'),
                        'Published':
                        st.column_config.TextColumn('Published'),
                        'Duration':
                        st.column_config.TextColumn('Duration')
                    }

            # Display filtered results
            st.dataframe(filtered_display_df[display_columns],
                         column_config=column_config,
                         hide_index=True,
                         use_container_width=True)

            # Download CSV button
            st.subheader("💾 Export Data")

            # Prepare CSV data
            csv_df = filtered_df[[
                'title', 'channel_title', 'view_count', 'published_date',
                'duration', 'video_url'
            ]].copy()
            csv_df.columns = [
                'Title', 'Channel', 'View Count', 'Published Date', 'Duration',
                'Video URL'
            ]

            csv_buffer = BytesIO()
            csv_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="📥 Download Search Results as CSV",
                data=csv_data,
                file_name=
                f"youtube_search_{search_query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="Download the search results as a CSV file",
                key="search_download")


def search_history_tab():
    st.header("📚 Search History")
    st.markdown("View and manage your previous searches")

    if not st.session_state.get('db_manager'):
        st.warning(
            "⚠️ Database not available. Search history requires database connection."
        )
        st.info(
            "Previous searches are stored in the database for easy access and comparison."
        )
        return

    try:
        db = st.session_state['db_manager']

        # Get search history
        search_history = db.get_search_history(limit=100)

        if not search_history:
            st.info(
                "📝 No search history found. Start by analyzing channels or searching for videos!"
            )
            return

        # Convert to DataFrame for better display
        history_df = pd.DataFrame(search_history)
        history_df['search_date'] = pd.to_datetime(
            history_df['search_date']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Display options
        st.subheader("🎛️ Display Options")

        col1, col2 = st.columns(2)

        with col1:
            search_type_filter = st.selectbox(
                "Filter by Type", ["All", "Channel Analysis", "Video Search"],
                key="history_type_filter")

        with col2:
            show_latest = st.slider("Number of Records",
                                    min_value=5,
                                    max_value=min(100, len(history_df)),
                                    value=min(20, len(history_df)),
                                    key="history_limit")

        # Apply filters
        filtered_history = history_df.copy()

        if search_type_filter == "Channel Analysis":
            filtered_history = filtered_history[filtered_history['search_type']
                                                == 'channel']
        elif search_type_filter == "Video Search":
            filtered_history = filtered_history[filtered_history['search_type']
                                                == 'video_search']

        # Limit results
        filtered_history = filtered_history.head(show_latest)

        # Display search history
        st.subheader("📋 Search History")

        # Format columns for display
        display_history = filtered_history.copy()
        display_history['Search Type'] = display_history['search_type'].map({
            'channel':
            'Channel Analysis',
            'video_search':
            'Video Search'
        })
        display_history['Query'] = display_history['search_query']
        display_history['Results'] = display_history['total_results']
        display_history['Date'] = display_history['search_date']

        # Select columns for display
        display_columns = ['Query', 'Search Type', 'Results', 'Date']
        column_config = {
            'Query': st.column_config.TextColumn('Search Query',
                                                 width='large'),
            'Search Type': st.column_config.TextColumn('Type'),
            'Results': st.column_config.NumberColumn('Results'),
            'Date': st.column_config.TextColumn('Date')
        }

        # Add action column
        if len(filtered_history) > 0:
            st.dataframe(display_history[display_columns],
                         column_config=column_config,
                         hide_index=True,
                         use_container_width=True)

            # Popular searches
            st.subheader("🔥 Popular Searches")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Popular Channel Searches:**")
                popular_channels = db.get_popular_searches('channel', limit=5)
                if popular_channels:
                    for search in popular_channels:
                        st.write(
                            f"• {search['search_query']} ({search['search_count']} times)"
                        )
                else:
                    st.write("No popular channel searches yet")

            with col2:
                st.markdown("**Popular Video Searches:**")
                popular_videos = db.get_popular_searches('video_search',
                                                         limit=5)
                if popular_videos:
                    for search in popular_videos:
                        st.write(
                            f"• {search['search_query']} ({search['search_count']} times)"
                        )
                else:
                    st.write("No popular video searches yet")

            # Export search history
            st.subheader("💾 Export History")

            # Prepare CSV data
            csv_buffer = BytesIO()
            history_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="📥 Download Search History as CSV",
                data=csv_data,
                file_name=
                f"youtube_search_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="Download your complete search history as a CSV file",
                key="history_download")
        else:
            st.info("No search history matches your filters.")

    except Exception as e:
        st.error(f"❌ Error loading search history: {str(e)}")
        st.info("Database connection might be lost. Try refreshing the page.")


if __name__ == "__main__":
    main()
