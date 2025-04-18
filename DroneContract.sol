// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

contract DroneConsensus {
    using ECDSA for bytes32;

    // --- 이벤트 정의 ---
    event BlockCommitted(
        uint256 indexed blockView,
        string operation,
        uint256 x,
        uint256 y,
        address signer
    );

    // --- 커밋된 블록 추적용 ---
    mapping(uint256 => bool) public committedViews;

    // --- 블록 커밋 함수 ---
    function commitBlockWithSig(
        uint256 blockView,
        string calldata operation,
        uint256 x,
        uint256 y,
        bytes calldata signature
    ) external {
        require(!committedViews[blockView], "Block already committed");

        bytes32 messageHash = keccak256(abi.encodePacked(blockView, operation, x, y));
        bytes32 ethSignedMessageHash = ECDSA.toEthSignedMessageHash(messageHash);

        address signer = ECDSA.recover(ethSignedMessageHash, signature);

        require(signer == msg.sender, "Sender and signer mismatch");

        committedViews[blockView] = true;

        emit BlockCommitted(blockView, operation, x, y, signer);
    }
}
