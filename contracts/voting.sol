// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PerfectVotingSystem {
    address public admin;

    // VotingSession stores the core details of a voting session.
    // Note that mappings cannot be iterated, so we keep an array of options for iteration.
    struct VotingSession {
        string name;                // Name or description of the session.
        string[] options;           // List of candidate or option names.
        uint256 startTime;          // When the voting starts.
        uint256 endTime;            // When the voting ends.
        bool resultsReleased;       // Flag to indicate if results are public.
        mapping(string => uint256) votesCount; // Mapping of option name to vote count.
        mapping(address => bool) hasVoted;       // Track if an address has voted.
        mapping(string => bool) validOptions;    // For duplicate prevention.
    }
    
    // We use an array to store sessions.
    VotingSession[] private sessions;
    
    // Events to log session creation, voting, and results release.
    event SessionCreated(uint indexed sessionId, string name, uint256 startTime, uint256 endTime);
    event Voted(uint indexed sessionId, address voter, string option);
    event ResultsReleased(uint indexed sessionId);
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }
    
    constructor() {
        admin = msg.sender;
    }
    
    /// @notice Creates a new voting session.
    /// @param _name The name or description of the session.
    /// @param _options The list of voting options.
    /// @param _duration Duration of the session (in seconds).
    function createVotingSession(
        string memory _name,
        string[] memory _options,
        uint256 _duration
    ) external onlyAdmin {
        require(_options.length > 0, "At least one option required");
        require(_duration > 0, "Duration must be positive");
        
        // Create a new session.
        sessions.push();
        uint256 sessionId = sessions.length - 1;
        VotingSession storage session = sessions[sessionId];
        session.name = _name;
        session.startTime = block.timestamp;
        session.endTime = block.timestamp + _duration;
        session.resultsReleased = false;
        
        // Populate options and ensure no duplicate options.
        for (uint256 i = 0; i < _options.length; i++) {
            string memory option = _options[i];
            require(!session.validOptions[option], "Duplicate option detected");
            session.options.push(option);
            session.validOptions[option] = true;
        }
        
        emit SessionCreated(sessionId, _name, session.startTime, session.endTime);
    }
    
    /// @notice Vote for a given option in a specific session.
    /// @param _sessionId The session identifier.
    /// @param _option The option (as a string) to vote for.
    function vote(uint256 _sessionId, string memory _option) external {
        require(_sessionId < sessions.length, "Invalid session ID");
        VotingSession storage session = sessions[_sessionId];
        
        require(block.timestamp >= session.startTime, "Voting has not started yet");
        require(block.timestamp <= session.endTime, "Voting has ended");
        require(session.validOptions[_option], "Invalid option");
        require(!session.hasVoted[msg.sender], "Already voted");
        
        session.votesCount[_option]++;
        session.hasVoted[msg.sender] = true;
        
        emit Voted(_sessionId, msg.sender, _option);
    }
    
    /// @notice Admin can release the results once the voting period has ended.
    /// @param _sessionId The session identifier.
    function releaseResults(uint256 _sessionId) external onlyAdmin {
        require(_sessionId < sessions.length, "Invalid session ID");
        VotingSession storage session = sessions[_sessionId];
        require(block.timestamp > session.endTime, "Voting period not ended");
        require(!session.resultsReleased, "Results already released");
        
        session.resultsReleased = true;
        emit ResultsReleased(_sessionId);
    }
    
    /// @notice Returns the results for a session. The results are accessible to the admin at any time,
    ///         and to others only after results are released.
    /// @param _sessionId The session identifier.
    /// @return options The list of options.
    /// @return counts The vote counts corresponding to each option.
    function getResults(uint256 _sessionId) external view returns (string[] memory options, uint256[] memory counts) {
        require(_sessionId < sessions.length, "Invalid session ID");
        VotingSession storage session = sessions[_sessionId];
        require(msg.sender == admin || session.resultsReleased, "Results not released yet");
        
        uint256 len = session.options.length;
        options = session.options;
        counts = new uint256[](len);
        for (uint256 i = 0; i < len; i++) {
            counts[i] = session.votesCount[session.options[i]];
        }
    }
    
    /// @notice Returns the total number of voting sessions created.
    function getSessionCount() external view returns (uint256) {
        return sessions.length;
    }
    
    /// @notice Checks if a given session is currently active.
    /// @param _sessionId The session identifier.
    /// @return True if the session is active, otherwise false.
    function isSessionActive(uint256 _sessionId) external view returns (bool) {
        require(_sessionId < sessions.length, "Invalid session ID");
        VotingSession storage session = sessions[_sessionId];
        return (block.timestamp >= session.startTime && block.timestamp <= session.endTime);
    }
}
