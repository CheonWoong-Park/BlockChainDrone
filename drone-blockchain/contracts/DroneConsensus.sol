// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DroneConsensus {
    event NewAuthorization(address client);
    event CommandValidated(address indexed sender, string operation);
    event BlockCommitted(uint256 blockView, string digest, string operation, uint256 x, uint256 y);

    address[] public authorizedClients;
    address public owner;
    mapping(uint256 => string) public committedBlocks;

    constructor() {
        owner = msg.sender;
        authorizedClients.push(owner);
    }

    function validateCommand(address sender, string calldata operation) 
        external returns (bool) {
        require(isAuthorized(sender), "Unauthorized client");
        require(!isMalicious(operation), "Malicious command");
        emit CommandValidated(sender, operation);
        return true;
    }

    function addAuthorizedClient(address newClient) external onlyOwner {
        authorizedClients.push(newClient);
        emit NewAuthorization(newClient);
    }

    function commitBlock(
        uint256 blockView,
        string calldata digest,
        string calldata operation,
        uint256 x,
        uint256 y
    ) external {
        require(bytes(committedBlocks[blockView]).length == 0, "Already committed");
        committedBlocks[blockView] = digest;
        emit BlockCommitted(blockView, digest, operation, x, y);
    }

    function isAuthorized(address client) public view returns (bool) {
        for(uint i = 0; i < authorizedClients.length; i++){
            if(authorizedClients[i] == client) return true;
        }
        return false;
    }

    function isMalicious(string calldata operation) public pure returns (bool) {
        return keccak256(bytes(operation)) == keccak256(bytes("malicious_cmd"));
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this");
        _;
    }

    modifier onlyAuthorized() {
        require(isAuthorized(msg.sender), "Unauthorized");
        _;
    }
}
