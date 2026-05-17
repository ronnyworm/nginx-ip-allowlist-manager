import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open, MagicMock

# Assuming your script is named allowlist_manager.py
from expire_ips import manage_allowlist

# Helper to create date strings
TODAY = datetime.now()
YESTERDAY = (TODAY - timedelta(days=1)).strftime("%Y-%m-%d")
TOMORROW = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")

@pytest.fixture
def mock_nginx_config():
    """Simulates a allowlist.conf with varied scenarios."""
    return (
        f"# expire after {YESTERDAY}\n"
        "allow 1.1.1.1;\n"
        f"# expire after {TOMORROW}\n"
        "allow 2.2.2.2;\n"
        "# expire never\n"
        "allow 3.3.3.3;\n"
        "deny all;\n"
    )

@patch("os.system")
@patch("os.path.exists")
@patch("shutil.move")
def test_manage_allowlist_logic(mock_move, mock_exists, mock_os_system, mock_nginx_config):
    # Setup mocks
    mock_exists.return_value = True
    mock_os_system.return_value = 0  # Simulate nginx -t success
    
    # We mock the open() calls for both reading and writing
    m = mock_open(read_data=mock_nginx_config)
    
    with patch("builtins.open", m):
        manage_allowlist()

    # Get all lines written to the temp file
    # writelines receives a list of lines
    written_lines = m.return_value.writelines.call_args.args[0]
    written_data = "".join(written_lines)

    # ASSERTIONS
    
    # 1. Check that the expired IP was commented out
    assert f"#allow 1.1.1.1;" in written_data
    
    # 2. Check that the future IP is still active
    assert "allow 2.2.2.2;" in written_data
    assert "#allow 2.2.2.2;" not in written_data
    
    # 3. Check that 'expire never' is untouched
    assert "allow 3.3.3.3;" in written_data
    
    # 4. Check that the final 'deny all' is untouched
    assert "deny all;" in written_data

    # 5. Verify Nginx was reloaded
    # Check if any call to os.system contained 'reload'
    reload_called = any("reload" in str(call) for call in mock_os_system.call_args_list)
    assert reload_called is True

@patch("os.path.exists")
def test_file_not_found(mock_exists):
    mock_exists.return_value = False
    
    # Should handle gracefully without crashing
    with patch("builtins.print") as mock_print:
        manage_allowlist()
        mock_print.assert_any_call("Error: /etc/nginx/conf.d/allowlist.conf not found.")

@patch("os.system")
@patch("os.path.exists")
@patch("shutil.move")
def test_nginx_syntax_error_prevents_reload(mock_move, mock_exists, mock_os_system, mock_nginx_config):
    mock_exists.return_value = True
    
    # Mock os.system so nginx -t fails (returns non-zero)
    def mock_system_calls(cmd):
        if "nginx -t" in cmd:
            return 1 # Error
        return 0
    
    mock_os_system.side_effect = mock_system_calls
    
    m = mock_open(read_data=mock_nginx_config)
    with patch("builtins.open", m), patch("builtins.print") as mock_print:
        manage_allowlist()
        
        # Verify reload was NEVER called because of the syntax error
        reload_called = any("reload" in str(call) for call in mock_os_system.call_args_list)
        assert reload_called is False
        error_msg_printed = any("Error: Nginx config check failed" in str(call) for call in mock_print.call_args_list)
        assert error_msg_printed is True
