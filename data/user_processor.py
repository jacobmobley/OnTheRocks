import backend.utils as backend_utils
from backend.ml_utils import suggest_drink

def get_user_with_history(user_id):
    """
    Get user and their drink history
    
    Args:
        user_id: Discord user ID
        
    Returns:
        tuple: (user, drink_history, drink_count)
    """
    user = backend_utils.upsert_user(user_id)
    user_drink_history = backend_utils.get_user_drink_history(user_id)
    drink_count = len(user_drink_history)
    
    return user, user_drink_history, drink_count

def determine_user_suggestion_strategy(drink_count, user_prefs, k_threshold=1):
    """
    Determine which suggestion strategy to use for a user
    
    Args:
        drink_count: Number of drinks user has logged
        user_prefs: User preference weights
        k_threshold: Minimum drinks needed for preference-based recommendations
        
    Returns:
        str: Strategy type ('popular' or 'preference')
    """
    if drink_count < k_threshold or not user_prefs:
        return 'popular'
    else:
        return 'preference'

def get_drink_suggestion_workflow(user_id, strategy, k=1):
    """
    Get drink suggestions based on strategy
    
    Args:
        user_id: Discord user ID
        strategy: Strategy type ('popular' or 'preference')
        k: Number of neighbors for KNN (default 1)
        
    Returns:
        List of up to k drink dicts (if preference), or a single dict (if popular)
    """
    if strategy == 'popular':
        return backend_utils.get_popular_drink_not_tried(user_id)
    else:
        user = backend_utils.upsert_user(user_id)
        logged_drinks = backend_utils.get_user_drink_history(user_id)
        return suggest_drink(user.prefs, k=k, logged_drinks=logged_drinks) 